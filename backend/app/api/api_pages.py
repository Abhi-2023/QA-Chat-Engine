from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="frontend/templates")


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
