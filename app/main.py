import json
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import numpy as np
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .models import HasilSegmentasi

BASE = Path(__file__).parent
MODEL_PATH = BASE.parent / "model" / "segmentasi_model.joblib"
INFO_PATH = BASE.parent / "model" / "model_info.json"

# ====== EDIT DATA KELOMPOK DI SINI ======
ANGGOTA = [
    {"nama": "Jojo", "nim": "NIM kamu", "peran": "Developer & Data Scientist"},
    {"nama": "Anggota 2", "nim": "NIM", "peran": "Frontend"},
    {"nama": "Anggota 3", "nim": "NIM", "peran": "Database"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Segmentasi Pelanggan Toko Online", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")

_model = None


def get_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    return _model


def get_info():
    return json.loads(INFO_PATH.read_text(encoding="utf-8")) if INFO_PATH.exists() else None


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"info": get_info(), "page": "home"})


@app.get("/contact")
def contact(request: Request):
    return templates.TemplateResponse(request, "contact.html", {"anggota": ANGGOTA, "page": "contact"})


@app.get("/prediksi")
def prediksi(request: Request, db: Session = Depends(get_db), pesan: str = "", error: str = ""):
    data = db.query(HasilSegmentasi).order_by(HasilSegmentasi.id.desc()).all()
    return templates.TemplateResponse(
        request, "prediksi.html",
        {"data": data, "pesan": pesan, "error": error, "model_ok": get_model() is not None, "page": "prediksi"},
    )


# CREATE: simpan input + hasil prediksi AI
@app.post("/prediksi")
def create(
    nama_pelanggan: str = Form(...),
    recency: int = Form(...),
    frequency: int = Form(...),
    monetary: float = Form(...),
    db: Session = Depends(get_db),
):
    model = get_model()
    if model is None:
        return RedirectResponse("/prediksi?error=Model belum ada. Jalankan train_model.py dulu.", status_code=303)
    if recency < 0 or frequency < 1 or monetary <= 0:
        return RedirectResponse("/prediksi?error=Input tidak valid (Recency>=0, Frequency>=1, Monetary>0).", status_code=303)

    x = model["scaler"].transform(np.log1p([[recency, frequency, monetary]]))
    cluster = int(model["kmeans"].predict(x)[0])
    segmen = model["cluster_labels"][cluster]

    db.add(HasilSegmentasi(
        nama_pelanggan=nama_pelanggan.strip(), recency=recency, frequency=frequency, monetary=monetary,
        cluster=cluster, segmen=segmen, strategi=model["strategi"][segmen],
    ))
    db.commit()
    return RedirectResponse(f"/prediksi?pesan=Berhasil! {nama_pelanggan} masuk segmen {segmen}.", status_code=303)


# DELETE: hapus data lewat halaman web
@app.post("/hapus/{item_id}")
def delete(item_id: int, db: Session = Depends(get_db)):
    item = db.get(HasilSegmentasi, item_id)
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse("/prediksi?pesan=Data berhasil dihapus.", status_code=303)
