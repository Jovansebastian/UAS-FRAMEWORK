from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .database import Base


class HasilSegmentasi(Base):
    __tablename__ = "hasil_segmentasi"

    id = Column(Integer, primary_key=True, index=True)
    nama_pelanggan = Column(String(100), nullable=False)
    recency = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    monetary = Column(Float, nullable=False)
    cluster = Column(Integer, nullable=False)
    segmen = Column(String(50), nullable=False)
    strategi = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
