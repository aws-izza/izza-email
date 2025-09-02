
import json
import os
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_FILE = "data/data.json"
PDF_DIR = "data/pdfs"

if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

class TableRow(BaseModel):
    sido: str
    sigungu: str
    yuhyeong: str
    danji_name: str
    gosi_date: str
    gosi_number: str
    gosi_name: str
    pdf: str

def read_data() -> List[TableRow]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        return [TableRow(**row) for row in data]

def write_data(data: List[TableRow]):
    with open(DATA_FILE, "w") as f:
        json.dump([row.model_dump() for row in data], f, indent=4)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    data = read_data()
    return templates.TemplateResponse("index.html", {"request": request, "data": data})

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request):
    data = read_data()
    return templates.TemplateResponse("admin.html", {"request": request, "data": data})

@app.post("/admin/add")
async def add_row(
    sido: str = Form(...),
    sigungu: str = Form(...),
    yuhyeong: str = Form(...),
    danji_name: str = Form(...),
    gosi_date: str = Form(...),
    gosi_number: str = Form(...),
    gosi_name: str = Form(...),
    pdf: UploadFile = File(...)
):
    data = read_data()
    pdf_path = os.path.join(PDF_DIR, pdf.filename)
    with open(pdf_path, "wb") as buffer:
        buffer.write(pdf.file.read())

    new_row = TableRow(
        sido=sido,
        sigungu=sigungu,
        yuhyeong=yuhyeong,
        danji_name=danji_name,
        gosi_date=gosi_date,
        gosi_number=gosi_number,
        gosi_name=gosi_name,
        pdf=pdf.filename
    )
    data.append(new_row)
    write_data(data)
    return {"message": "Row added successfully"}


@app.get("/download/{pdf_name}")
async def download_pdf(pdf_name: str):
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_name)
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
