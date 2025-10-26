
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from .db import Base
import datetime

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200))

    timesheets = relationship("Timesheet", back_populates="employee")

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    client = Column(String(200))

    tasks = relationship("Task", back_populates="job")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    name = Column(String(200), nullable=False)
    notes = Column(Text)

    job = relationship("Job", back_populates="tasks")

class CalendarEvent(Base):
    __tablename__ = 'calendar_events'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    title = Column(String(200), nullable=False)
    note = Column(Text)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))

class Timesheet(Base):
    __tablename__ = 'timesheets'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    note = Column(Text)

    employee = relationship("Employee", back_populates="timesheets")
