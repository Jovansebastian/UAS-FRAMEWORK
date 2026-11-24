"""
SOAL 1 - Training model AI (K-Means) untuk segmentasi pelanggan berbasis RFM.
Jalankan:  python train_model.py
Dataset : taruh file Online Retail II (.xlsx atau .csv) di folder data/
"""
import json
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
MODEL_DIR = BASE / "model"
IMG_DIR = BASE / "app" / "static" / "img"
K_FINAL = 4  # jumlah segmen akhir (4 segmen gampang dijelaskan secara bisnis)

SEGMENT_NAMES = ["Champions", "Loyal", "Berpotensi", "Hampir Hilang"]
STRATEGI = {
    "Champions": "Pelanggan terbaik: baru belanja, sering, dan nilainya besar. Beri reward eksklusif, akses produk lebih awal, dan program referral.",
    "Loyal": "Pelanggan setia yang rutin belanja. Tawarkan program poin/membership, bundling, dan upsell produk bernilai lebih tinggi.",
    "Berpotensi": "Pelanggan dengan potensi tumbuh. Kirim rekomendasi produk personal, diskon terbatas, dan dorong belanja ulang.",
    "Hampir Hilang": "Sudah lama tidak belanja dan jarang bertransaksi. Jalankan kampanye win-back: voucher comeback dan survei alasan berhenti.",
}


def load_raw() -> pd.DataFrame:
    files = sorted([*DATA_DIR.glob("*.xlsx"), *DATA_DIR.glob("*.xls"), *DATA_DIR.glob("*.csv")])
    if not files:
        raise SystemExit("Dataset tidak ditemukan! Taruh file Online Retail II (.xlsx/.csv) di folder 'data/'.")
    f = files[0]
    print(f"[1/6] Membaca dataset: {f.name} (kalau .xlsx bisa 1-3 menit, sabar ya)")
    if f.suffix == ".csv":
        try:
            df = pd.read_csv(f, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(f, encoding="ISO-8859-1")
    else:
        df = pd.concat(pd.read_excel(f, sheet_name=None).values(), ignore_index=True)
    df = df.rename(columns={"InvoiceNo": "Invoice", "UnitPrice": "Price", "CustomerID": "Customer ID"})
    return df


def main():
    MODEL_DIR.mkdir(exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_raw()
    n_raw = len(raw)

    # ---------- Preprocessing ----------
    print("[2/6] Preprocessing data...")
    df = raw.dropna(subset=["Customer ID"]).copy()
    df["Invoice"] = df["Invoice"].astype(str)
    df = df[~df["Invoice"].str.startswith("C")]  # buang transaksi pembatalan
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Total"] = df["Quantity"] * df["Price"]

    snapshot = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("Customer ID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
        Frequency=("Invoice", "nunique"),
        Monetary=("Total", "sum"),
    ).reset_index()
    rfm = rfm[rfm["Monetary"] > 0]

    # log transform (data RFM sangat miring) lalu standardisasi
    X_log = np.log1p(rfm[["Recency", "Frequency", "Monetary"]])
    scaler = StandardScaler()
    X = scaler.fit_transform(X_log.values)

    # ---------- Cari K terbaik ----------
    print("[3/6] Mencari jumlah cluster (Elbow + Silhouette)...")
    ks, inertias, sils = list(range(2, 9)), [], []
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        inertias.append(float(km.inertia_))
        sils.append(float(silhouette_score(X, km.labels_, sample_size=min(5000, len(X)), random_state=42)))
        print(f"      k={k}  inertia={inertias[-1]:.1f}  silhouette={sils[-1]:.3f}")

    # ---------- Training & Evaluasi ----------
    print(f"[4/6] Training model final K-Means (k={K_FINAL})...")
    kmeans = KMeans(n_clusters=K_FINAL, n_init=10, random_state=42).fit(X)
    rfm["Cluster"] = kmeans.labels_
    metrics = {
        "silhouette_score": round(float(silhouette_score(X, kmeans.labels_)), 4),
        "davies_bouldin_index": round(float(davies_bouldin_score(X, kmeans.labels_)), 4),
        "calinski_harabasz": round(float(calinski_harabasz_score(X, kmeans.labels_)), 2),
        "inertia": round(float(kmeans.inertia_), 2),
    }
    print("      Evaluasi:", metrics)

    # ---------- Beri nama segmen berdasarkan profil RFM ----------
    prof = rfm.groupby("Cluster").agg(
        Recency=("Recency", "median"), Frequency=("Frequency", "median"),
        Monetary=("Monetary", "median"), Jumlah=("Customer ID", "count"),
    )
    prof["score"] = (
        prof["Recency"].rank(ascending=False) + prof["Frequency"].rank() + prof["Monetary"].rank()
    )
    order = prof.sort_values(["score", "Monetary"], ascending=False).index.tolist()
    cluster_labels = {int(c): SEGMENT_NAMES[i] for i, c in enumerate(order)}
    clusters_info = [
        {
            "cluster": int(c),
            "segmen": cluster_labels[int(c)],
            "jumlah": int(prof.loc[c, "Jumlah"]),
            "recency": round(float(prof.loc[c, "Recency"]), 1),
            "frequency": round(float(prof.loc[c, "Frequency"]), 1),
            "monetary": round(float(prof.loc[c, "Monetary"]), 2),
        }
        for c in order
    ]

    # ---------- Simpan model ----------
    print("[5/6] Menyimpan model...")
    joblib.dump(
        {"scaler": scaler, "kmeans": kmeans, "cluster_labels": cluster_labels, "strategi": STRATEGI},
        MODEL_DIR / "segmentasi_model.joblib",
    )
    info = {
        "dataset": {
            "baris_mentah": int(n_raw),
            "baris_bersih": int(len(df)),
            "jumlah_pelanggan": int(len(rfm)),
            "negara": int(df["Country"].nunique()) if "Country" in df else None,
            "tanggal_awal": str(df["InvoiceDate"].min().date()),
            "tanggal_akhir": str(df["InvoiceDate"].max().date()),
        },
        "model": {"algoritma": "K-Means", "k": K_FINAL, "fitur": ["Recency", "Frequency", "Monetary"]},
        "metrics": metrics,
        "elbow": [{"k": k, "inertia": round(i, 1), "silhouette": round(s, 4)} for k, i, s in zip(ks, inertias, sils)],
        "clusters": clusters_info,
    }
    (MODEL_DIR / "model_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    # ---------- Grafik ----------
    print("[6/6] Membuat grafik...")
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    ax[0].plot(ks, inertias, "o-", color="#4f46e5"); ax[0].axvline(K_FINAL, ls="--", color="#ef4444")
    ax[0].set_title("Elbow Method"); ax[0].set_xlabel("K"); ax[0].set_ylabel("Inertia")
    ax[1].plot(ks, sils, "o-", color="#10b981"); ax[1].axvline(K_FINAL, ls="--", color="#ef4444")
    ax[1].set_title("Silhouette Score"); ax[1].set_xlabel("K")
    plt.tight_layout(); plt.savefig(IMG_DIR / "elbow.png", dpi=130); plt.close()

    plt.figure(figsize=(6, 4.5))
    for c in order:
        m = rfm["Cluster"] == c
        plt.scatter(np.log1p(rfm.loc[m, "Frequency"]), np.log1p(rfm.loc[m, "Monetary"]), s=8, alpha=.6, label=cluster_labels[int(c)])
    plt.xlabel("log(1+Frequency)"); plt.ylabel("log(1+Monetary)"); plt.title("Sebaran Segmen Pelanggan")
    plt.legend(markerscale=2); plt.tight_layout(); plt.savefig(IMG_DIR / "cluster.png", dpi=130); plt.close()

    print("\nSELESAI. Model tersimpan di model/segmentasi_model.joblib")


if __name__ == "__main__":
    main()
