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