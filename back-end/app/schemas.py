# app/schemas.py
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    company_name: str

class UserOut(BaseModel):
    id: int
    username: str
    company_name: str

    class Config:
        orm_mode = True
class File(BaseModel):
    content: str
    company_name: str
class File_with_job(BaseModel):
    content: str
    company_name: str
    job_name: str
class File_with_id(BaseModel):
    telegram_id: str
    content: str

class Candidate(BaseModel):
    telegram_id: str
    user_name: str


class Job(BaseModel):
    name: str
    file: str
    company_name: str

class Company(BaseModel):
    name: str

class Company_and_Job(BaseModel):
    company_name: str
    job_name: str

class Job_with_id(BaseModel):
    id: int
    name: str
    company_name: str
class Job_name(BaseModel):
    name: str
    company_name: str
class User_tg_id(BaseModel):
    telegram_id: str

class User_tg_id_and_company(BaseModel):
    telegram_id: str
    company_name: str

class User_tg_id_and_job(BaseModel):
    telegram_id: str
    job: str
    company_name: str

class Candidate_with_score(BaseModel):
    telegram_id: str
    score: float

class Candidate_with_lang(BaseModel):
    telegram_id: str
    lang: str