from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.books import router as books_router
from app.routes.members import router as members_router
import json
import os

BOOKS_FILE = "books.json"
MEMBERS_FILE = "members.json"

def load_books():
    if not os.path.exists(BOOKS_FILE):
        return []
    with open(BOOKS_FILE, "r") as f:
        return json.load(f)

def load_members():
    if not os.path.exists(MEMBERS_FILE):
        return []
    with open(MEMBERS_FILE, "r") as f:
        return json.load(f)

app = FastAPI(title="Library Manager")

# Any request that arrives at the (/static/... ) address, find the corresponding file from the app/static folder and return it.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(books_router, prefix="/books")
app.include_router(members_router, prefix="/members")

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def root(request: Request):
    books = load_books()
    members = load_members()
    # --- COMPUTE STATISTICS HERE ---
    # total_books
    total_books = len(books)
    # available_books
    available_books = sum(1 for book in books if not book.get("is_loaned", False))
    # loaned_books
    loaned_books = sum(1 for book in books if book.get("is_loaned", False))
    # total_members
    total_members = len(members)
    # unique_authors
    unique_authors = len(set(b["author"] for b in books))
    # oldest_book, newest_book
    if books:
        oldest_book = min(books, key=lambda b: b.get("year", float('inf')))
        newest_book = max(books, key=lambda b: b.get("year", float('-inf')))
    else:
        oldest_book = None
        newest_book = None
        
    print (oldest_book , newest_book)
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={
            "total_books": total_books,
            "available_books": available_books,
            "loaned_books": loaned_books,
            "total_members": total_members,
            "unique_authors": unique_authors,
            "oldest_title": oldest_book['title'],
            "oldest_year": oldest_book['year'],
            "newest_title": newest_book['title'],
            "newest_year": newest_book['year'],
        }
    )