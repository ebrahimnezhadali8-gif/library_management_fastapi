from urllib import request
from fastapi import APIRouter, Request, Form, status, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
import os
import json
import math

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

BOOKS_FILE = "books.json"
ITEMS_PER_PAGE = 5

def load_books():
    if not os.path.exists(BOOKS_FILE):
        return []
    with open(BOOKS_FILE, "r") as f:
        return json.load(f)

@router.get("/landing", response_class=HTMLResponse)
async def books_landing(
    request: Request,
    sort: str = Query("default", pattern="^(default|title|author|year)$"),
    page: int = Query(1, ge=1),
    search: str = Query(None)
):
    books = load_books()
    # search
    if search:
        search_lower = search.lower()
        filtered = []
        for b in books:
            if (search_lower in b["title"].lower() or
                search_lower in b["author"].lower() or
                search_lower in b["isbn"].lower()):
                filtered.append(b)
        books = filtered
        
    # Step 2: Apply sorting
    if sort == "title":
        books = sorted(books, key=lambda x: x["title"].lower())
    elif sort == "author":
        books = sorted(books, key=lambda x: x["author"].lower())
    elif sort == "year":
        books = sorted(books, key=lambda x: x["year"])
        
     # Step 3: Pagination
    total_items = len(books)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated_books = books[start:end]
    
    if page > total_pages and total_pages > 0:
        return RedirectResponse(
            url=f"/books/landing?sort={sort}&page={total_pages}&search={search or ''}",
            status_code=303
        )
    
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
    
   # Check for duplicate ISBN
    for book in books:
        if book["isbn"] == isbn:
            # error message for duplicate ISBN
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
    
    # Create new book entry
    new_book = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "year": year,
        "is_loaned": is_loaned,
        "loaned_to": loaned_to if is_loaned else None
    }
    books.append(new_book)
    with open(BOOKS_FILE, "w") as f:
        json.dump(books, f, indent=4)
    
    # After saving, redirect to the books list page
    return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)

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
    book_isbn: str,
    title: str = Form(...),
    author: str = Form(...),
    year: int = Form(...),
    is_loaned: bool = Form(False),
    loaned_to: str = Form("")
):
    books = load_books()
    current_year = datetime.now().year

    # validatiion years
    if year < 1800 or year > current_year:
        original_book = None
        for b in books:
            if b["isbn"] == book_isbn:
                original_book = b
                break
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
            with open(BOOKS_FILE, "w") as f:
                json.dump(books, f, indent=4)
            return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="Book not found")

# show page delete 
@router.get("/delete/{book_isbn}", response_class=HTMLResponse)
async def confirm_delete(request: Request, book_isbn: str):
    books = load_books()
    book = None
    for b in books:
        if b["isbn"] == book_isbn:
            book = b
            break
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse(
        request=request,
        name="books/book_delete.html",
        context={"book": book}
    )

#  delete
@router.post("/delete/{book_isbn}")
async def delete_book(book_isbn: str):
    books = load_books()
    new_books = [book for book in books if book["isbn"] != book_isbn]
    if len(new_books) == len(books):
        raise HTTPException(status_code=404, detail="Book not found")
    with open(BOOKS_FILE, "w") as f:
        json.dump(new_books, f, indent=4)
    return RedirectResponse("/books/landing", status_code=status.HTTP_303_SEE_OTHER)