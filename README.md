# Segmentasi Pelanggan Toko Online (RFM + K-Means)
FastAPI + Jinja2 + CSS/JS + scikit-learn + PostgreSQL/MySQL

## Langkah menjalankan (VS Code terminal)
1. Buat virtual env & install:
   python -m venv venv
   venv\Scripts\activate          (Windows)   |   source venv/bin/activate (Mac/Linux)
   pip install -r requirements.txt
2. Download dataset "Online Retail II" (UCI) -> taruh file .xlsx/.csv di folder `data/`
3. Edit `.env` -> ganti PASSWORD_KAMU dengan password PostgreSQL kamu (database & tabel dibuat otomatis, atau manual lewat database.sql)
4. Training model (Soal 1):
   python train_model.py
5. Jalankan website (Soal 2 & 3):
   uvicorn app.main:app --reload
6. Buka http://127.0.0.1:8000

Edit anggota kelompok di `app/main.py` (variabel ANGGOTA).
