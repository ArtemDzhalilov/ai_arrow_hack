# app/main.py
import os
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Form, BackgroundTasks, Query
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
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
import io
import wave
from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer
import subprocess
from fastapi.middleware.cors import CORSMiddleware
import torchaudio
from speechbrain.pretrained import EncoderClassifier

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:7000,http://localhost:7000,http://127.0.0.1:8501,http://localhost:8501",
    ).split(",")
    if origin.strip()
]
GAME_PUBLIC_URL = os.getenv("GAME_PUBLIC_URL", "http://127.0.0.1:7000/game")

models.Base.metadata.create_all(bind=engine)

app1 = FastAPI()

app1.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
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


@app1.get('/redirect')
def redirect(user_tg_id: str = Query(...), db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    room_id = crud.get_room_id(user_tg=user_tg_id, db=db)
    player_id = crud.get_player_id(user_tg=user_tg_id, db=db)

    # Формируем JSON параметры, которые будут переданы
    json_params = {
        'campaign_id': [room_id],
        'player_id': [player_id]
    }
    external_url = GAME_PUBLIC_URL

    # HTML с встроенным скриптом для отправки данных
    html_content = f"""
            <html>
                <body>
                    <h1>Redirecting...</h1>
                    <form id="redirectForm" action="{external_url}" method="POST">
                        <input type="hidden" name="campaign_id" value='{room_id}' />
                        <input type="hidden" name="player_id" value='{player_id}' />
                    </form>
                    <script type="text/javascript">
                        // Автоматически отправляем форму после загрузки страницы
                        document.getElementById('redirectForm').submit();
                    </script>
                </body>
            </html>
            """
    background_tasks.add_task(celery_score_softskills, room_id=room_id, user_tg=user_tg_id)
    return HTMLResponse(content=html_content, status_code=200)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app1,
        host="0.0.0.0",
        port=10000,
    )
