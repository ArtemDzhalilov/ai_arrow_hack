# app/main.py
import torch
from fastapi import FastAPI, Depends, HTTPException, Form, BackgroundTasks, Query
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import hashlib
from celery_app import score_resume as celery_score_resume
from celery_app import celery_score_softskills
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydub import AudioSegment
import os
import io
import wave
from vosk import Model, KaldiRecognizer
import subprocess
from fastapi.middleware.cors import CORSMiddleware
import torchaudio
from speechbrain.pretrained import EncoderClassifier
from TTS.api import TTS

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:7000"],  # Замените на URL вашего frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or user.hashed_password != hashlib.sha256(form_data.password.encode()).hexdigest():
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {'company_name': user.company_name}


@app.post("/score_resume")
def score_resume(candidate: schemas.File_with_id, db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    background_tasks.add_task(celery_score_resume, content=candidate.content, telegram_id=candidate.telegram_id)
    return JSONResponse(status_code=200, content={'message': 'Resume scored successfully'})


@app.post("/create_job")
def create_job(job: schemas.Job, db: Session = Depends(get_db)):
    job = crud.create_job(job=job, db=db)
    if not job:
        raise HTTPException(status_code=500, detail="Cannot create job")
    return JSONResponse(status_code=200, content={'message': 'Job created successfully'})
@app.delete("/delete_job")
def delete_job(job: schemas.Job_name, db: Session = Depends(get_db)):
    job = crud.delete_job(job=job, db=db)
    if not job:
        raise HTTPException(status_code=500, detail="Job not found")
    return JSONResponse(status_code=200, content={'message': 'Job deleted successfully'})
@app.post("/create_file")
def create_file(file: schemas.File_with_job, db: Session = Depends(get_db)):
    file = crud.create_file(file=file, db=db)
    if not file:
        raise HTTPException(status_code=500, detail="Cannot create file")
    return JSONResponse(status_code=200, content={'message': 'File created successfully'})

@app.get('/get_jobs_by_company_name')
def get_jobs_by_company_name(company: schemas.Company, db: Session = Depends(get_db)):
    company_name = company.name
    jobs = crud.get_jobs_by_company_name(company_name=company_name, db=db)
    if not jobs:
        raise HTTPException(status_code=500, detail="Jobs not found")
    return jobs
@app.post("/register_candidate")
def register_candidate(candidate: schemas.Candidate, db: Session = Depends(get_db)):
    candidates = crud.get_candidates_by_telegram_id(telegram_id=candidate.telegram_id, db=db)
    if candidates:
        raise HTTPException(status_code=403, detail="Candidate already registered")
    candidate = crud.create_candidate(candidate=candidate, db=db)
    if not candidate:
        raise HTTPException(status_code=500, detail="Cannot create candidate")
    return JSONResponse(status_code=200, content={'message': 'Candidate created successfully'})
@app.get('/get_candidates_by_job_name')
def get_candidates_by_job_name(job: schemas.Job_with_id, db: Session = Depends(get_db)):
    job_name = job.name
    company_name = job.company_name
    candidates = crud.get_candidates_by_job_name(job_name=job_name,company_name=company_name, db=db)
    return candidates
@app.get('/check_company')
def check_company(company: schemas.Company, db: Session = Depends(get_db)):
    company_name = company.name
    company = crud.get_company_by_name(company_name=company_name, db=db)
    if not company:
        return JSONResponse(status_code=500, content={'exists': False})
    return JSONResponse(status_code=200, content={'exists': True})
@app.get('/check_job')
def check_job_name(job: schemas.Job_name, db: Session = Depends(get_db)):
    job = crud.check_job_name(job=job, db=db)
    if not job:
        return JSONResponse(status_code=500, content={'exists': False})
    return JSONResponse(status_code=200, content={'exists': True})
@app.get('/get_user_data')
def get_user_data(user_tg: schemas.User_tg_id, db: Session = Depends(get_db)):

    user = crud.get_candidate_by_telegram_id(telegram_id=user_tg.telegram_id, db=db)
    if not user:
        return JSONResponse(status_code=500, content={'exists': False})
    return user

@app.post('/add_user_to_company')
def add_user_to_company(tg_and_company: schemas.User_tg_id_and_company, db: Session = Depends(get_db)):
    user = crud.add_user_to_company(user_tg=tg_and_company.telegram_id, company_name=tg_and_company.company_name, db=db)
    print(user)
    if not user:
        return JSONResponse(status_code=500, content={'exists': False})
    return JSONResponse(status_code=200, content={'exists': True})

@app.post('/add_user_to_job')
def add_user_to_job(data: schemas.User_tg_id_and_job, db: Session = Depends(get_db)):
    user = crud.add_user_to_job(user_tg=data.telegram_id, job_name=data.job, db=db)
    if not user:
        return JSONResponse(status_code=500, content={'exists': False})
    return JSONResponse(status_code=200, content={'exists': True})
@app.get('/get_requirements')
def get_requirements(job: schemas.Job_name, db: Session = Depends(get_db)):
    content = crud.get_requirements(job=job, db=db)
    if not content:
        return JSONResponse(status_code=500, content={'exists': False})
    return JSONResponse(status_code=200, content={'requirements': content})
@app.post('/update_hardskills_score')
def update_hardskills_score(cand: schemas.Candidate_with_score, db: Session = Depends(get_db)):
    content = crud.update_hardskills_score(cand=cand, db=db)
    if not content:
        return JSONResponse(status_code=500, content={'exists': False})
    return content
@app.get('/get_user_language')
def get_user_language(user_tg: schemas.User_tg_id, db: Session = Depends(get_db)):
    content = crud.get_user_language(user_tg=user_tg.telegram_id, db=db)
    if not content:
        return JSONResponse(status_code=500, content={'exists': False})
    return content
@app.post('/set_user_language')
def set_user_language(cand: schemas.Candidate_with_lang, db: Session = Depends(get_db)):
    content = crud.set_user_language(user_tg=cand.telegram_id, lang=cand.lang, db=db)
    if not content:
        return JSONResponse(status_code=500, content={'exists': False})
    return content
@app.post('/start_dnd_game')
def start_dnd_game(user_tg: schemas.User_tg_id, db: Session = Depends(get_db)):
    availible_rooms = crud.get_available_campaigns(db=db)
    if availible_rooms is None or len(availible_rooms) == 0:
        room_id = crud.create_campaign(db=db)
    else:
        print(availible_rooms)
        room_id = availible_rooms[0].id_real
    res = crud.create_player(room_id=room_id, telegram_id=user_tg.telegram_id, db=db)
    link = f"http://83.239.141.6:27280/redirect?user_tg_id={user_tg.telegram_id}"
    return link



@app.post('/finalize')
def finalize(cand: schemas.User_tg_id, db: Session = Depends(get_db)):
    content = crud.finalize(tg_id=cand, db=db)
    if not content:
        return JSONResponse(status_code=500, content={'exists': False})
    return content

vosk_model_en = Model("vosk-model-en-us-0.22")
vosk_model_ru = Model("vosk-model-ru-0.42")
language_id = EncoderClassifier.from_hparams(source="TalTechNLP/voxlingua107-epaca-tdnn", savedir="tmp")
@app.post("/transcribe_audio")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    try:
        # Сохранение аудиофайла
        with open("temp_audio.webm", "wb") as f:
            f.write(await audio_file.read())

        # Конвертация WebM в WAV с помощью ffmpeg
        subprocess.run(["ffmpeg", "-i", "temp_audio.webm", "temp_audio.wav", "-y"])

        # Транскрибация аудио
        wf = wave.open("temp_audio.wav", "rb")
        #signal = language_id.load_audio("/home/hellstrom/folder/aiarrow-hackaton-2024/back-end/app/temp_audio.wav")
        #prediction = language_id.classify_batch(signal)
        #if prediction[3] == "ru":
        #    rec = KaldiRecognizer(vosk_model_ru, wf.getframerate())
        #else:
        #    rec = KaldiRecognizer(vosk_model_en, wf.getframerate())
        rec = KaldiRecognizer(vosk_model_en, wf.getframerate())
        rec.SetWords(True)

        result = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result += rec.Result()

        # Добавление финального результата
        result += rec.FinalResult()
        print("")
        print("Transcription:")
        print('_____________________')
        print(result)

        # Удаление временных файлов
        os.remove("temp_audio.webm")
        os.remove("temp_audio.wav")

        # Возврат результата в формате JSON
        return {"transcription": result}

    except Exception as e:
        print(e)
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )