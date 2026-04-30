from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

URL_BASE_DATOS = "sqlite:///./cyberlab.db"

engine = create_engine(URL_BASE_DATOS, connect_args={"check_same_thread": False})
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()