-- PostgreSQL: jalankan lewat pgAdmin (Query Tool) atau psql
-- Langkah 1: bikin database (jalankan saat konek ke database "postgres")
CREATE DATABASE segmentasi_db;

-- Langkah 2: konek ke segmentasi_db, lalu jalankan bagian ini
-- (opsional, karena tabel juga dibuat otomatis saat web dijalankan)
CREATE TABLE IF NOT EXISTS hasil_segmentasi (
    id              SERIAL PRIMARY KEY,
    nama_pelanggan  VARCHAR(100) NOT NULL,
    recency         INTEGER      NOT NULL,
    frequency       INTEGER      NOT NULL,
    monetary        DOUBLE PRECISION NOT NULL,
    cluster         INTEGER      NOT NULL,
    segmen          VARCHAR(50)  NOT NULL,
    strategi        TEXT         NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_hasil_segmentasi_id ON hasil_segmentasi (id);
