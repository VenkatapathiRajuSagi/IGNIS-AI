import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./fire_alerts.db"

Base = declarative_base()

class AlertLog(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    confidence = Column(Float)
    alert_type = Column(String)  # Fire or Smoke
    image_path = Column(String, nullable=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def log_alert(confidence, alert_type, image_path=None):
    db = SessionLocal()
    try:
        alert = AlertLog(confidence=confidence, alert_type=alert_type, image_path=image_path)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    finally:
        db.close()

def get_recent_alerts(limit=10):
    db = SessionLocal()
    try:
        return db.query(AlertLog).order_by(AlertLog.timestamp.desc()).limit(limit).all()
    finally:
        db.close()
