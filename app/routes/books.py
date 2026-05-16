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
BOOKS_FILE = "books.json"
ITEMS_PER_PAGE = 5

def load_books():
    if not os.path.exists(BOOKS_FILE):
        return []
    with open(BOOKS_FILE, "r") as f:
        return json.load(f)