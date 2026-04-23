import os
from pathlib import Path
from random import choice

from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from openai import OpenAI
import torch
from torch.nn.functional import cosine_similarity

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

OPENAI_UNAVAILABLE = "OpenAI API key is not configured or the request failed."
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

model_name = "second-state/E5-Mistral-7B-Instruct-Embedding-GGUF"
model_file = "e5-mistral-7b-instruct-Q6_K.gguf"
model_path = hf_hub_download(model_name, filename=model_file)

llm = Llama(
    model_path=model_path,
    n_ctx=16000,
    n_threads=32,
    n_gpu_layers=0,
    embedding=True,
)


def score_resume(anchor, candidate):
    with torch.no_grad():
        embedding1 = llm.embed(anchor)
        embedding2 = llm.embed(candidate)
        embedding1 = torch.Tensor([embedding1]).mean(1)
        embedding2 = torch.Tensor([embedding2]).mean(1)
        score = cosine_similarity(embedding1, embedding2, dim=1)
        return score.item()


def create_initial_stories(prompt: str = "") -> list:
    prompt = prompt or ""
    world_type = [
        "fantasy",
        "sci-fi",
        "medieval",
        "cyberpunk",
        "post-apocalyptic",
        "steampunk",
        "futuristic",
        "dystopian",
        "utopian",
        "magical",
        "mystical",
        "mythical",
        "legendary",
        "historical",
        "modern",
    ]
    render_format = ". Write it using the HTML formats when underlining or bolding. No other format is allowed."

    try:
        return continue_history_gpt(
            f"Tell me a story about a {choice(world_type)} world where i have to defeat some strong enemies and bosses to win, this is a initial story of a game. Also tell me at least three names of key bosses and it's race and class to be defeated, and why i have to defeat them. Don't talk about a protagonist or a specific hero, just leave it like a mission to fulfill for 'anyone' or 'you (talking to the player)'. "
            + prompt
            + render_format
        )
    except Exception:
        return "Sorry, no story"


def continue_history_gpt(prompt):
    if openai_client is None:
        return OPENAI_UNAVAILABLE

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception:
        return OPENAI_UNAVAILABLE


def generate_best_softskills(job_requirements):
    prompt = (
        "Lets think step by step. You are psychologist and your task to generate best soft skills for the job requirements. "
        "It must be only a list of adjectives that describe soft skills. Job requirements: "
        + job_requirements
    )
    return continue_history_gpt(prompt)


def check_softskills(history_text, user_name):
    prompt = (
        "Lets think step by step. You are psychologist and your task to check soft skills. "
        "You must check soft skills that user has by analyzing his dungeons and dragons game. "
        "It must be only a list of adjectives that describe soft skills. "
        f"User name: {user_name}. Game history: {history_text}"
    )
    return continue_history_gpt(prompt)


def get_soft_skills_score(history_text, user_name, job_requirements):
    best_softskills = generate_best_softskills(job_requirements)
    user_softskills = check_softskills(history_text, user_name)
    softskills_score = score_resume(best_softskills, user_softskills)
    return softskills_score
