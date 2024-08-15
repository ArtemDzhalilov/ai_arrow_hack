import logging
import time

from celery import Celery
from database import SessionLocal, engine
from schemas import File_with_id
from models import File, Candidate
from ml import score_resume as score_resume_ml
from ml import get_soft_skills_score
import dnd_module as dnd

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Celery(
    'tasks',
    broker='redis://127.0.0.1:6379/0',
    backend='redis://127.0.0.1:6379/0'
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.task
def score_resume(content: str, telegram_id: str):
    try:
        db = next(get_db())

        text_cadidate = content
        cand = db.query(Candidate).filter(Candidate.telegram_id == telegram_id).first()
        text_anchor = db.query(File).filter(File.company_name == cand.company_name).filter(File.job_name == cand.job_name).first().content

        resume_score = score_resume_ml(text_anchor, text_cadidate)


        db.query(Candidate).filter(Candidate.telegram_id == telegram_id).update({Candidate.resume_score: resume_score})
        db.commit()

        return resume_score
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)
        raise

@app.task
def celery_score_softskills(room_id: int, user_tg: str):
    time.sleep(120)
    db = next(get_db())
    job_name = db.query(Candidate).filter(Candidate.telegram_id == user_tg).first().job_name
    job_requirements = db.query(File).filter(File.job_name == job_name).first().content
    room_history = dnd.get_room_history(room_id)
    print(room_history)
    soft_skills_score = get_soft_skills_score(room_history, user_tg, job_requirements)

    db.query(Candidate).filter(Candidate.telegram_id == user_tg).update({Candidate.soft_skills_score: soft_skills_score})
    db.commit()

    return soft_skills_score



