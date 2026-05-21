# 📚 Library Management System

A simple web application for managing books and library members with lending/return capabilities.  
Built with **FastAPI**, **Jinja2 Templates**, **JSON** for data storage, and **UV** for dependency management.

---

## ✨ Features

### Books
- Add new book with year validation (between 1800 and current year)
- Edit book details (ISBN cannot be changed)
- Delete book with confirmation page
- Search books by title, author, or ISBN
- Sort by title, author, or year
- Pagination (5 books per page) preserving sort and search
- Display status: `Available` or `Loaned to member X`

### Members
- Add new member with auto‑generated ID (M001, M002, …)
- Email validation (must contain `@`)
- Edit and delete members
- Search by member ID, name, or email
- Sort by ID, name, or email
- Pagination similar to books

### Loan System
- Loan a book to a member (dedicated page with dropdown member selection)
- Return a book with one click
- Record loan date and return date in `loans.json`
- Prevent deletion of a member who has active loans
- Show number of currently loaned books on member profile page
- List active loans on member profile page

### Dashboard
- Statistics: total books, available books, loaned books, total members
- Number of unique authors
- Oldest and newest book in the library

---

## 🛠️ Technologies Used

- **FastAPI** – web framework
- **Jinja2** – template engine
- **UV** – dependency management and runner (replaces `pip` + `venv`)
- **JSON** – file‑based storage (no database)
- **Font Awesome** – icons
- **Custom CSS** – modern, responsive styling

---

## 🚀 How to Run (using UV)

### 1. Prerequisites
- Python 3.12 or higher
- Install **UV**

#### Install UV (Windows, Linux, macOS):
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

2. Get the project
    git clone https://github.com/ebrahimnezhadali8-gif/library_management_fastapi
    cd library_management

3. Install dependencies with UV

    uv sync

4. Run the development server

    uv run uvicorn app.main:app --reload --port 8000
Or : 
    uvicorn app.main:app --reload

5. Open in your browser
- Dashboard: http://localhost:8000
- Automatic API docs: http://localhost:8000/docs
- Books management: http://localhost:8000/books/landing
- Members management: http://localhost:8000/members/landing


```
-----
## 📝 Important Notes
- Data is stored in JSON files – they are created automatically on first use.
- Deleting a member with active loans is forbidden and will raise an error.
- Loan is allowed only for books that are available.
- Book year must be between 1800 and the current year.
- Member email must contain the @ character.

## 🧪 Quick Test
1. Add a new book with status "Available".
2. Add a new member (ID is auto‑generated).
3. In the book list, click the Loan button.
4. Select a member from the dropdown and confirm.
5. The book status changes to Loaned to M00X and appears in the member's profile.
6. Click Return to bring the book back.

## 🤝 Developer
This project was built as a hands‑on exercise to learn FastAPI, CRUD operations, pagination, search, sorting, and a loan system with file‑based storage.

Happy coding!