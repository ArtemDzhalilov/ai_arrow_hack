# back-end/models.py
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    company_name = Column(String)

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    company_name = Column(String)
    job_name = Column(String)

class Candidate(Base):
    __tablename__ = 'candidates'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True)
    user_name = Column(String)
    company_name = Column(String, autoincrement=False)
    job_name = Column(String, autoincrement=False)
    resume_score = Column(Float, autoincrement=False)
    hard_skills_score = Column(Float, autoincrement=False)
    soft_skills_score = Column(Float, autoincrement=False)
    result_score = Column(Float, autoincrement=False)
    lang = Column(String, default='en')

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    company_name = Column(String)


class Campaign(Base):
    __tablename__ = 'campaigns1'
    id = Column(Integer, primary_key=True, index=True)
    id_real = Column(Integer)
    player1 = Column(String, autoincrement=False)
    player1_id = Column(Integer, autoincrement=False)
    player2 = Column(String, autoincrement=False)
    player2_id = Column(Integer, autoincrement=False)
    player3 = Column(String, autoincrement=False)
    player3_id = Column(Integer, autoincrement=False)
    player4 = Column(String, autoincrement=False)
    player4_id = Column(Integer, autoincrement=False)
    player5 = Column(String, autoincrement=False)
    player5_id = Column(Integer, autoincrement=False)