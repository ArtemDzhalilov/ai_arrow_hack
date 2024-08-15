# back-end/crud.py
from sqlalchemy.orm import Session
import models, schemas
from hashlib import sha256
import dnd_module
from sqlalchemy import or_

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = sha256(user.password.encode()).hexdigest()
    db_user = models.User(username=user.username, hashed_password=hashed_password, company_name=user.company_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_file(db: Session, file: schemas.File_with_job):
    db_file = models.File(content=file.content, company_name=file.company_name, job_name=file.job_name)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def create_job(db: Session, job: schemas.Job):
    db_job = models.Job(name=job.name, company_name=job.company_name)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job
def delete_job(db: Session, job: schemas.Job_name):
    db_job = db.query(models.Job).filter(models.Job.name == job.name).filter(models.Job.company_name == job.company_name).first()
    db.delete(db_job)
    db.commit()
    return db_job
def get_jobs_by_company_name(db: Session, company_name: str):
    return db.query(models.Job).filter(models.Job.company_name == company_name).all()
def get_candidates_by_job_name(db: Session, job_name: str, company_name: str):
    return db.query(models.Candidate).filter(models.Candidate.company_name == company_name).filter(models.Candidate.job_name == job_name).all()

def create_candidate(db: Session, candidate: schemas.Candidate):
    db_candidate = models.Candidate(telegram_id=candidate.telegram_id, user_name=candidate.user_name)
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate
def get_company_by_name(db: Session, company_name: str):
    return db.query(models.User).filter(models.User.company_name == company_name).first()

def check_job_name(db: Session, job: schemas.Job_name):
    return db.query(models.Job).filter(models.Job.name == job.name).filter(models.Job.company_name == job.company_name).first()

def get_candidates_by_telegram_id(db: Session, telegram_id: str):
    return db.query(models.Candidate).filter(models.Candidate.telegram_id == telegram_id).first()

def get_candidate_by_telegram_id(db: Session, telegram_id: str):
    return db.query(models.Candidate).filter(models.Candidate.telegram_id == telegram_id).first()
def add_user_to_company(db: Session, user_tg: str, company_name: str):
    db_user = db.query(models.Candidate).filter(models.Candidate.telegram_id == user_tg).first()
    db_user.company_name = company_name
    db.commit()
    db.refresh(db_user)
    return db_user
def add_user_to_job(db: Session, user_tg: str, job_name: str):
    db_user = db.query(models.Candidate).filter(models.Candidate.telegram_id == user_tg).first()
    db_user.job_name = job_name
    db.commit()
    db.refresh(db_user)
    return db_user

def get_requirements(db: Session, job: schemas.Job_name):
    job_name = job.name
    company_name = job.company_name
    return db.query(models.File).filter(models.File.company_name == company_name).filter(models.File.job_name == job_name).first().content
def update_hardskills_score(db: Session, cand: schemas.Candidate_with_score):
    db_user = db.query(models.Candidate).filter(models.Candidate.telegram_id == cand.telegram_id).first()
    db_user.hard_skills_score = cand.score
    db.commit()
    db.refresh(db_user)
    return db_user
def get_user_language(db: Session, user_tg: str):
    print(user_tg)
    db_user = db.query(models.Candidate).filter(models.Candidate.telegram_id == user_tg).first()
    return db_user.lang
def set_user_language(db: Session, user_tg: str, lang: str):
    db_user = db.query(models.Candidate).filter(models.Candidate.telegram_id == user_tg).first()
    db_user.lang = lang
    db.commit()
    db.refresh(db_user)
    return db_user

def get_available_campaigns(db: Session):
    return db.query(models.Campaign).filter(models.Campaign.player5 == None).all()
def create_campaign(db: Session):
    real_id = dnd_module.create_campaign()
    db_campaign = models.Campaign(id_real=real_id)
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign
def get_availible_players(db: Session, room_id: int):
    campaigns = db.query(models.Campaign).filter(models.Campaign.id_real == room_id).first()
    if campaigns.player1 is None:
        return 1
    elif campaigns.player2 is None:
        return 2
    elif campaigns.player3 is None:
        return 3
    elif campaigns.player4 is None:
        return 4
    elif campaigns.player5 is None:
        return 5
    return campaigns
def create_player(db: Session, room_id: int, telegram_id: str):
    campaign = db.query(models.Campaign).filter(models.Campaign.id_real == room_id).first()
    player_id = dnd_module.create_player_dnd(room_id, telegram_id)
    print(telegram_id)
    print(campaign.player1, campaign.player2, campaign.player3, campaign.player4, campaign.player5)
    if campaign.player1 is None:
        campaign.player1 = telegram_id
        campaign.player1_id = player_id
    elif campaign.player2 is None:
        campaign.player2 = telegram_id
        campaign.player2_id = player_id
    elif campaign.player3 is None:
        campaign.player3 = telegram_id
        campaign.player3_id = player_id
    elif campaign.player4 is None:
        campaign.player4 = telegram_id
        campaign.player4_id = player_id
    elif campaign.player5 is None:
        campaign.player5 = telegram_id
        campaign.player5_id = player_id
    db.commit()
    db.refresh(campaign)
    return campaign
def get_room_id(db: Session, user_tg: str):
    print(user_tg)
    real_id = db.query(models.Campaign).filter(or_(
        models.Campaign.player1 == user_tg,
        models.Campaign.player2 == user_tg,
        models.Campaign.player3 == user_tg,
        models.Campaign.player4 == user_tg,
        models.Campaign.player5 == user_tg
    )
    ).first().id_real
    return real_id
def get_player_id(db: Session, user_tg: str):
    print(user_tg)
    player_id = db.query(models.Campaign).filter(models.Campaign.player1 == user_tg).first().player1_id
    if player_id is not None:
        return player_id
    player_id = db.query(models.Campaign).filter(models.Campaign.player2 == user_tg).first().player2_id
    if player_id is not None:
        return player_id
    player_id = db.query(models.Campaign).filter(models.Campaign.player3 == user_tg).first().player3_id
    if player_id is not None:
        return player_id
    player_id = db.query(models.Campaign).filter(models.Campaign.player4 == user_tg).first().player4_id
    if player_id is not None:
        return player_id
    player_id = db.query(models.Campaign).filter(models.Campaign.player5 == user_tg).first().player5_id
    if player_id is not None:
        return player_id

def finalize(tg_id: schemas.User_tg_id, db: Session):
    cand = db.query(models.Candidate).filter(models.Candidate.telegram_id == tg_id.telegram_id).first()
    final_score = (cand.hard_skills_score + cand.resume_score+cand.soft_skills_score) / 3
    cand.result_score = final_score
    db.commit()
    db.refresh(cand)
    return cand


