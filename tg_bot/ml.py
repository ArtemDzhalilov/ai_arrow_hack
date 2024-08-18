import time
import torch
import torch.nn.functional as F
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from torch.nn.functional import cosine_similarity
import openai
import logging
openai.api_key = ""
lang_dict = {
    'ru': 'Russian',
    'en': 'English',
}

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
llm_new = Llama(
    model_path=new_model_path,
    n_ctx=4096,
    n_threads=1,
    n_gpu_layers=98,
    use_mlock=True,
    flash_attn=True,
    f16_kv=False,
)
print("All is ready!")


# Функция для тестирования скорости работы модели
def test_model_speed(model, prompt="Test prompt"):
    start_time = time.time()
    response = model(prompt, max_tokens=50)
    elapsed_time = time.time() - start_time
    return elapsed_time


#local_model_time = test_model_speed(llm_old)
# Если локальная модель работает медленнее 10 секунд, переключаемся на использование OpenAI API
#if local_model_time > 10:
#    print("Local model is slow, switching to GPT-4 API...")
#    use_openai_api = True
#else:
#    print("Using local model.")
#    use_openai_api = False
use_openai_api = True

def generate_role(requirements):
    prompt = f"Generate the role that best fits the LLM for an interview based on the following description: {requirements}. Output ONLY the role."

    if use_openai_api:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are an AI assistant."},
                          {"role": "user", "content": prompt}],
            )
            return response['choices'][0]['message']['content'].strip()
        except:
            return 'OpenAI API is not available in your country.'
    else:
        response = llm_new(prompt)
        return response['choices'][0]['text'].strip()


def create_question_with_answer(history, requirements, lang):
    history_text = f"During the interview, the following questions have already been asked, and the following answers have been received: {history}." if len(
        history) > 0 else ""
    role = generate_role(requirements)
    prompt = f"""You are conducting an interview for the position of {role}. Job description: {requirements}. {history_text}
    Your task is to generate the next question so that it best fits the job description and assesses the interviewee's competencies in the most critical areas. The question should have a clear answer and focus solely on algorithms and data structures.
    You should generate only the question. You must use {lang_dict[lang]} in your question. 
    """

    if use_openai_api:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are an AI assistant."},
                          {"role": "user", "content": prompt}],
            )
            question = response['choices'][0]['message']['content'].strip()
        except:
            return 'OpenAI API is not available in your country.', 'OpenAI API is not available in your country.'
    else:
        response = llm_new(prompt)
        question = response['choices'][0]['text'].strip()

    answer = answer_question(question, role, lang_dict[lang])
    return question, answer


def answer_question(question, role, lang):
    prompt = f"""
    You are one of the best {role} in the world, and you are interviewing at an IT company. Your task is to answer the following question as accurately as possible: {question}. Your answer should be concise and precise. You only need to answer the question. You must use {lang} in your question.  
"""

    if use_openai_api:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are an AI assistant."},
                          {"role": "user", "content": prompt}],
            )
            return response['choices'][0]['message']['content'].strip()
        except:
            return 'OpenAI API is not available in your country.'
    else:
        response = llm_new(prompt)
        return response['choices'][0]['text'].strip()
def translate_to_english(text):
    prompt = f"Translate the following text to English: {text}"
    if use_openai_api:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are an AI assistant."},
                          {"role": "user", "content": prompt}],
            )
            return response['choices'][0]['message']['content'].strip()
        except:
            return 'OpenAI API is not available in your country.'
    else:
        response = llm_new(prompt)
        return response['choices'][0]['text'].strip()


def compare_answers(user_answer, correct_answer, lang):
    if lang == 'ru':
        user_answer = translate_to_english(user_answer)
        correct_answer = translate_to_english(correct_answer)
    with torch.no_grad():
        if correct_answer=='OpenAI API is not available in your country.':
            return 0
        embedding1 = llm_old.embed(user_answer)
        embedding2 = llm_old.embed(correct_answer)
        embedding1 = torch.Tensor([embedding1]).mean(1)
        embedding2 = torch.Tensor([embedding2]).mean(1)
        score = cosine_similarity(embedding1, embedding2, dim=1)
        return score.item()
