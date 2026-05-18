from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form, status
from fastapi.responses import RedirectResponse
from fastapi import HTTPException
import json
import os
import math

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
MEMBERS_FILE = "members.json"
ITEMS_PER_PAGE = 5

def load_members():
    if not os.path.exists(MEMBERS_FILE):
        return []
    with open(MEMBERS_FILE, "r") as f:
        return json.load(f)
    
def save_members(members):
    with open(MEMBERS_FILE, "w") as f:
        json.dump(members, f, indent=4)
    
# generate member_id    
def next_member_id(members):
    if not members:
        return "M001"
    max_num = max(int(m["member_id"][1:]) for m in members)
    return f"M{max_num + 1:03d}"

# List members with sort/search/pagination
@router.get("/landing", response_class=HTMLResponse)
async def members_landing(
    request: Request,
    sort: str = Query("default", pattern="^(default|member_id|name|email)$"),
    page: int = Query(1, ge=1),
    search: str = Query(None)
):
    members = load_members()
    # search (member_id, name, email)
    if search:
        search_lower = search.lower()
        filtered = []
        for m in members:
            if (search_lower in m["member_id"].lower() or
                search_lower in m["name"].lower() or
                search_lower in m["email"].lower()):
                filtered.append(m)
        members = filtered

    # Sort 
    if sort == "member_id":
        members = sorted(members, key=lambda x: x["member_id"])
    elif sort == "name":
        members = sorted(members, key=lambda x: x["name"].lower())
    elif sort == "email":
        members = sorted(members, key=lambda x: x["email"].lower())

    total_items = len(members)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1

    if page > total_pages and total_pages > 0:
        return RedirectResponse(
            url=f"/members/landing?sort={sort}&page={total_pages}&search={search or ''}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated_members = members[start:end] if total_items > 0 else []

    return templates.TemplateResponse(
        request=request,
        name="members/members_landing.html",
        context={
            "members": paginated_members,
            "total_items": total_items,
            "current_page": page,
            "total_pages": total_pages,
            "sort": sort,
            "search": search if search else "",
        }
    )

# Show add member form
@router.get("/add", response_class=HTMLResponse)
async def add_member_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="members/member_form.html",
        context={
            "editing": False,
            "member": None,
            "member_id": None
        }
    )

# Create new member
@router.post("/", response_class=HTMLResponse)
async def create_member(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...)
):
    members = load_members()
    new_id = next_member_id(members)

    new_member = {
        "member_id": new_id,
        "name": name,
        "email": email,
        "phone": phone
    }
    members.append(new_member)
    save_members(members)

    return RedirectResponse("/members/landing", status_code=status.HTTP_303_SEE_OTHER)

# Show edit member form
@router.get("/edit/{member_id}", response_class=HTMLResponse)
async def edit_member_form(request: Request, member_id: str):
    members = load_members()
    member = None
    for m in members:
        if m["member_id"] == member_id:
            member = m
            break
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return templates.TemplateResponse(
        request=request,
        name="members/member_form.html",
        context={
            "editing": True,
            "member": member,
            "member_id": member_id
        }
    )


# Update member
@router.post("/{member_id}")
async def update_member(
    member_id: str,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...)
):
    members = load_members()
    for i, m in enumerate(members):
        if m["member_id"] == member_id:
            members[i] = {
                "member_id": member_id,
                "name": name,
                "email": email,
                "phone": phone
            }
            save_members(members)
            return RedirectResponse("/members/landing", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="Member not found")

# Show delete confirmation  
@router.get("/delete/{member_id}", response_class=HTMLResponse)
async def confirm_delete(request: Request, member_id: str):
    members = load_members()
    member = None
    for m in members:
        if m["member_id"] == member_id:
            member = m
            break
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return templates.TemplateResponse(
        request=request,
        name="members/member_delete.html",
        context={"member": member}
    )

# Delete member
@router.post("/delete/{member_id}")
async def delete_member(member_id: str):
    members = load_members()
    new_members = [m for m in members if m["member_id"] != member_id]
    if len(new_members) == len(members):
        raise HTTPException(status_code=404, detail="Member not found")
    save_members(new_members)
    return RedirectResponse("/members/landing", status_code=status.HTTP_303_SEE_OTHER)

