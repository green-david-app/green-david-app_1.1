
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import current_app

engine = None
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False))
Base = declarative_base()
Base.query = db_session.query_property()

def init_engine():
    global engine
    if engine is None:
        uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
        engine = create_engine(uri, connect_args={"check_same_thread": False})
    return engine

def init_db():
    from .models import Employee, Job, Task, CalendarEvent, Timesheet
    engine = init_engine()
    Base.metadata.create_all(bind=engine)
    db_session.configure(bind=engine)
