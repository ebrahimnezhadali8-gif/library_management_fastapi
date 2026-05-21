from fastapi import APIRouter, Request, Form, status, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, date
import os
import json
import math
from app.routes.loans import load_loans, save_loans, next_loan_id, get_loan_by_book_isbn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

BOOKS_FILE = "books.json"
ITEMS_PER_PAGE = 5

def load_books():
    if not os.path.exists(BOOKS_FILE):
        return []
    with open(BOOKS_FILE, "r") as f:
        return json.load(f)

def save_books(books):
    with open(BOOKS_FILE, "w") as f:
        json.dump(books, f, indent=4)

@router.get("/landing", response_class=HTMLResponse)
async def books_landing(
    request: Request,
    sort: str = Query("default", pattern="^(default|title|author|year)$"),
    page: int = Query(1, ge=1),
    search: str = Query(None)
):
    books = load_books()
    if search:
        search_lower = search.lower()
        filtered = []
        for b in books:
            if (search_lower in b["title"].lower() or
                search_lower in b["author"].lower() or
                search_lower in b["isbn"].lower()):
                filtered.append(b)
        books = filtered

    if sort == "title":
        books = sorted(books, key=lambda x: x["title"].lower())
    elif sort == "author":
        books = sorted(books, key=lambda x: x["author"].lower())
    elif sort == "year":
        books = sorted(books, key=lambda x: x["year"])

    total_items = len(books)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1

    if page > total_pages and total_pages > 0:
        return RedirectResponse(
            url=f"/books/landing?sort={sort}&page={total_pages}&search={search or ''}",
            status_code=303
        )

    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated_books = books[start:end] if total_items > 0 else []

    return templates.TemplateResponse(
        request=request,
        name="books/books_landing.html",
        context={
            "books": paginated_books,
            "total_items": total_items,
            "current_page": page,
            "total_pages": total_pages,
            "sort": sort,
            "search": search or "",
        }
    )

@router.get("/add", response_class=HTMLResponse)
async def add_book_form(request: Request):
    current_year = datetime.now().year
    return templates.TemplateResponse(
        request=request,
        name="books/book_form.html",
        context={
            "editing": False,
            "book": None,
            "book_isbn": None,
            "current_year": current_year
        }
    )

@router.post("/", response_class=HTMLResponse)
async def create_book(
    request: Request,
    isbn: str = Form(...),
    title: str = Form(...),
    author: str = Form(...),
    year: int = Form(...),
    is_loaned: bool = Form(False),
    loaned_to: str = Form("")
):
    books = load_books()
    current_year = datetime.now().year
    # validation years
    if year < 1800 or year > current_year:
        error_msg = f"Year must be between 1800 and {current_year}."
        return templates.TemplateResponse(
            request=request,
            name="books/book_form.html",
            context={
                "editing": False,
                "book": None,
                "book_isbn": None,
                "error": error_msg,
                "form_data": {
                    "isbn": isbn,
                    "title": title,
                    "author": author,
                    "year": year,
                    "is_loaned": is_loaned,
                    "loaned_to": loaned_to
                }
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    for book in books:
        if book["isbn"] == isbn:
            error_msg = f"A book with ISBN '{isbn}' already exists. Please use a different ISBN."
            return templates.TemplateResponse(
                request=request,
                name="books/book_form.html",
                context={
                    "editing": False,
                    "book": None,
                    "book_isbn": None,
                    "error": error_msg,
                    "form_data": {
                        "isbn": isbn,
                        "title": title,
                        "author": author,
                        "year": year,
                        "is_loaned": is_loaned,
                        "loaned_to": loaned_to
                    }
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )

    new_book = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "year": year,
        "is_loaned": is_loaned,
        "loaned_to": loaned_to if is_loaned else None
    }
    books.append(new_book)
    save_books(books)
    return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)

# loan book form
@router.get("/loan/{isbn}", response_class=HTMLResponse)
async def loan_book_form(request: Request, isbn: str):
    books = load_books()
    book = next((b for b in books if b["isbn"] == isbn), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["is_loaned"]:
        return RedirectResponse(url="/books/landing?error=already_loaned", status_code=303)
    
    from app.routes.members import load_members
    members = load_members()
    
    return templates.TemplateResponse(
        request=request,
        name="books/book_loan.html",
        context={
            "book": book,
            "members": members
        }
    )

@router.get("/edit/{book_isbn}", response_class=HTMLResponse)
async def edit_book_form(request: Request, book_isbn: str):
    books = load_books()
    book = next((b for b in books if b["isbn"] == book_isbn), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    current_year = datetime.now().year
    return templates.TemplateResponse(
        request=request,
        name="books/book_form.html",
        context={
            "editing": True,
            "book": book,
            "book_isbn": book_isbn,
            "current_year": current_year
        }
    )

@router.post("/{book_isbn}")
async def update_book(
    request: Request,
    book_isbn: str,
    title: str = Form(...),
    author: str = Form(...),
    year: int = Form(...),
    is_loaned: bool = Form(False),
    loaned_to: str = Form("")
):
    books = load_books()
    current_year = datetime.now().year

    if year < 1800 or year > current_year:
        original_book = next((b for b in books if b["isbn"] == book_isbn), None)
        error_msg = f"Year must be between 1800 and {current_year}."
        return templates.TemplateResponse(
            request=request,
            name="books/book_form.html",
            context={
                "editing": True,
                "book": original_book,
                "book_isbn": book_isbn,
                "error": error_msg,
                "form_data": {
                    "title": title,
                    "author": author,
                    "year": year,
                    "is_loaned": is_loaned,
                    "loaned_to": loaned_to
                }
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    for i, book in enumerate(books):
        if book["isbn"] == book_isbn:
            books[i] = {
                "isbn": book_isbn,
                "title": title,
                "author": author,
                "year": year,
                "is_loaned": is_loaned,
                "loaned_to": loaned_to if is_loaned else None
            }
            save_books(books)
            return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="Book not found")

@router.get("/delete/{book_isbn}", response_class=HTMLResponse)
async def confirm_delete(request: Request, book_isbn: str):
    books = load_books()
    book = next((b for b in books if b["isbn"] == book_isbn), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse(
        request=request,
        name="books/book_delete.html",
        context={"book": book}
    )

@router.post("/delete/{book_isbn}")
async def delete_book(book_isbn: str):
    books = load_books()
    new_books = [book for book in books if book["isbn"] != book_isbn]
    if len(new_books) == len(books):
        raise HTTPException(status_code=404, detail="Book not found")
    save_books(new_books)
    return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)

# loan book get form
@router.get("/loan/{isbn}", response_class=HTMLResponse)
async def loan_book(request: Request, isbn: str):
    books = load_books()
    book = next((b for b in books if b["isbn"] == isbn), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["is_loaned"]:
        raise HTTPException(status_code=400, detail="Book is already loaned")

    form_data = await request.form()
    member_id = form_data.get("member_id")
    if not member_id:
        raise HTTPException(status_code=400, detail="Member ID is required")

    from app.routes.members import load_members
    members = load_members()
    member = next((m for m in members if m["member_id"] == member_id), None)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # update book status
    book["is_loaned"] = True
    book["loaned_to"] = member_id
    save_books(books)

    # register loan
    loans = load_loans()
    new_loan = {
        "loan_id": next_loan_id(loans),
        "book_isbn": isbn,
        "member_id": member_id,
        "loan_date": date.today().isoformat(),
        "return_date": None
    }
    loans.append(new_loan)
    save_loans(loans)

    return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/return/{isbn}")
async def return_book(isbn: str):
    books = load_books()
    book = next((b for b in books if b["isbn"] == isbn), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book["is_loaned"]:
        raise HTTPException(status_code=400, detail="Book is not loaned")

    # close loan
    loan = get_loan_by_book_isbn(isbn)
    if loan:
        loans = load_loans()
        for l in loans:
            if l["loan_id"] == loan["loan_id"]:
                l["return_date"] = date.today().isoformat()
                break
        save_loans(loans)

    # update book status
    book["is_loaned"] = False
    book["loaned_to"] = None
    save_books(books)

    return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)