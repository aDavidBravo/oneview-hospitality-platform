import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://oneview_user:oneview_secret_2024@postgres:5432/oneview")
MODELS_PATH = os.getenv("MODELS_PATH", "/app/models")
FORECAST_HORIZON = int(os.getenv("FORECAST_HORIZON_DAYS", 14))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
