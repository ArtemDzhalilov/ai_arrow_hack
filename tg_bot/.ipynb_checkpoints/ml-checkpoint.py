import torch
import torch.nn.functional as F
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from torch.nn.functional import cosine_similarity
import logging


# Загрузка старой модели для эмбеддингов
old_model_name = "second-state/E5-Mistral-7B-Instruct-Embedding-GGUF"
old_model_file = "e5-mistral-7b-instruct-Q6_K.gguf"
old_model_path = hf_hub_download(old_model_name, filename=old_model_file)
llm_old = Llama(
    model_path=old_model_path,
    n_ctx=16000,
    n_threads=32,
    n_gpu_layers=0,
    embedding=True
)

new_model_name = "lmstudio-community/gemma-2-27b-it-GGUF"
new_model_file = "gemma-2-27b-it-Q6_K.gguf"
new_model_path = hf_hub_download(new_model_name, filename=new_model_file)
print(new_model_path)
llm_new = Llama(
    model_path=new_model_path,
    n_ctx=4096,
    n_threads=1,
    n_gpu_layers=0
)
print("All is ready!")

def generate_role(requirements):
    prompt = f"Сгенерируй роль, которая лучше всего подойдёт llm при прохождении собеседования на роль со следующим описанием. Выведи ТОЛЬКО роль: {requirements}"
    response = llm_new(prompt, max_tokens=150)
    return response['choices'][0]['text'].strip()

def create_question_with_answer(history, requirements):
    history_text = f"В течении интервью уже были заданы следующие вопросы и получены следующие ответы: {history}." if len(history) > 0 else ""
    role = generate_role(requirements)
    prompt = f"""
    Ты проводишь алгоритмическое интервью на должность {role}. Описание вакансии: {requirements}. {history_text} 
    Твоя задача - сгенерировать следующlogging.basicConfig(level=logging.DEBUG)ий вопрос так, чтобы он максимально подходил под описание вакансии, а также проверял компетенции интервьюируемого в самых нужных областях. Вопрос должен иметь однозначный ответ, и затрагивать только алгоритмы и структуры данных.
    Ты должен сгенерировать только вопрос.
    """
    response = llm_new(prompt, max_tokens=150)
    print(response['choices'][0])
    question = response['choices'][0]['text'].strip()
    answer = answer_question(question, role)
    return question, answer

def answer_question(question, role):
    prompt = f"""
    Ты один из лучших {role} в мире и ты собеседуешься в IT компанию, твоя задача максимально точно ответить на следующий вопрос: {question}. Твой ответ должен быть максимально кратким и точным. Тебе нужно только ответить на вопрос.
    """
    response = llm_new(prompt, max_tokens=150)
    return response['choices'][0]['text'].strip()

def compare_answers(user_answer, correct_answer):
    with torch.no_grad():
        # Используем старую модель для создания эмбеддингов
        embedding1 = llm_old.embed(user_answer)
        embedding2 = llm_old.embed(correct_answer)
        embedding1 = torch.Tensor([embedding1]).mean(1)
        embedding2 = torch.Tensor([embedding2]).mean(1)
        score = cosine_similarity(embedding1, embedding2, dim=1)
        return score.item()