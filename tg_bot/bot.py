import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
import random
import requests
from ml import *
from vosk import Model, KaldiRecognizer
import wave
import io
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import asyncio
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
from stt import STT

API_TOKEN = '7316928282:AAEw4DLPo6cAwMgFQ1fIcBPuw550qZj-2us'
BACKEND_URL = 'http://localhost:8000'

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Определение состояний


async def check_backend(endpoint, data):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{BACKEND_URL}/{endpoint}', json=data) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

async def get_backend_data(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{BACKEND_URL}/get_user_data', json={'telegram_id': str(user_id)}) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

async def add_user_to_company(user_id, company_name):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BACKEND_URL}/add_user_to_company', json={'telegram_id': str(user_id), 'company_name': company_name}) as resp:
            return resp.status == 200

async def start_user_registration(user_id, name):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BACKEND_URL}/register_candidate', json={'telegram_id': str(user_id), 'user_name': name}) as resp:
            return resp.status == 200

async def add_user_to_job(data):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BACKEND_URL}/add_user_to_job', json=data) as resp:
            return resp.status == 200
async def score_resume_request(content, user_id):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BACKEND_URL}/score_resume', json={'content': content, 'telegram_id': str(user_id)}) as resp:
            if resp.status == 200:
                return await resp.json()
            return None
async def get_requirements_request(data):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{BACKEND_URL}/get_requirements', json=data) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

async def start_dnd_game(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BACKEND_URL}/start_dnd_game', json={'telegram_id': str(user_id)}) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

async def finalize_interview(telegram_id):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BACKEND_URL}/finalize', json={'telegram_id': str(telegram_id)}) as resp:
            if resp.status == 200:
                return await resp.json()
            return None




# Определение состояний
class Form(StatesGroup):
    waiting_for_company_name = State()
    waiting_for_job_title = State()
    waiting_for_resume = State()
    waiting_for_hardskill_answer = State()
    waiting_for_softskills_check = State()
    waiting_for_language_selection = State()

# Словарь переводов для различных сообщений
translations = {
    'en': {
        'welcome': "Welcome! You have been registered.",
        'registration_failed': "Registration failed. Please try again later.",
        'select_company': "Please write company name to bot.",
        'company_exists': "Company exists and is selected.",
        'company_not_exist': "Company does not exist. Try again or type /select_company to start over.",
        'provide_job_title': "Please provide a job title.",
        'job_exists': "Job exists and is selected.",
        'job_not_exist': "Job does not exist. Try again or type /select_vacancy to start over.",
        'resume_prompt': "Please reply to this message with your resume file.",
        'resume_valid': "Resume is valid and checked.",
        'resume_invalid': "Resume is not valid. Please try again.",
        'hardskills_prompt': "Starting hard skills assessment. Answer the following question (you can answer using both voice and text):",
        'hardskills_invalid': "An error occured during the hard skills assessment. Please try again.",
        'answer_accepted': "Your answer has been accepted.",
        'next_question': "Next question:",
        'skills_assessment_complete': "Skills assessment completed.",
        'finalize_prompt': "Please complete all previous steps before finalizing.",
        'finalize_success': "Interview process finalized successfully.",
        'finalize_failed': "Failed to finalize the interview process.",
        'select_language_prompt': "Please select a language:",
        'language_selected': "Language selected: English",
        'select_company_first': "Please select a company first using /select_company.",
        'select_job_first': "Please select a job first using /select_vacancy.",
        'check_resume_first': "Please check your resume first using /score_resume.",
        'check_hardskills_first': "Please check your hard skills first using /check_hardskills.",
        'softskills_prompt': 'This is your link to game. Please copy it and paste in your browser.',
        'interview_finished': "Sorry, you have already completed the interview. Please wait for the results from the organizers.",
        'finalize_warning': "After finalizing, you will NOT BE ABLE TO change your answers",

    },
    'ru': {
        'welcome': "Добро пожаловать! Вы зарегистрированы.",
        'registration_failed': "Регистрация не удалась. Попробуйте позже.",
        'select_company': "Пожалуйста, напишите название компании.",
        'company_exists': "Компания существует и выбрана.",
        'company_not_exist': "Компания не существует. Попробуйте снова или введите /select_company, чтобы начать заново.",
        'provide_job_title': "Пожалуйста, укажите название вакансии.",
        'job_exists': "Вакансия существует и выбрана.",
        'job_not_exist': "Вакансия не существует. Попробуйте снова или введите /select_vacancy, чтобы начать заново.",
        'resume_prompt': "Пожалуйста, отправьте ваш резюме в ответ на это сообщение.",
        'resume_valid': "Резюме действительно и проверено.",
        'resume_invalid': "Резюме недействительно. Пожалуйста, попробуйте снова.",
        'hardskills_prompt': "Начинаем проверку профессиональных навыков. Ответьте на следующий вопрос:",
        'hardskills_invalid': "Произошла ошибка при проверке профессиональных навыков. Пожалуйста, попробуйте снова.",
        'answer_accepted': "Ваш ответ принят.",
        'next_question': "Следующий вопрос:",
        'skills_assessment_complete': "Оценка навыков завершена.",
        'finalize_prompt': "Пожалуйста, завершите все предыдущие шаги перед финализацией.",
        'finalize_success': "Процесс собеседования успешно завершен.",
        'finalize_failed': "Не удалось завершить процесс собеседования.",
        'select_language_prompt': "Пожалуйста, выберите язык:",
        'language_selected': "Выбран язык: Русский",
        'select_company_first': "Сначала выберите компанию с помощью /select_company.",
        'select_job_first': "Сначала выберите вакансию с помощью /select_vacancy.",
        'check_resume_first': "Сначала проверьте ваше резюме с помощью /score_resume.",
        'check_hardskills_first': "Сначала проверьте свои профессиональные навыки с помощью /check_hardskills.",
        'softskills_prompt': 'Это ваша ссылка на игру. Пожалуйста, скопируйте её и вставьте в ваш браузер.',
        'interview_finished': 'Вы не можете приступить к собеседованию так как Вы его уже проходили. Ожидайте результатов от организаторов.',
        'finalize_warning': 'После завершения, вы НЕ СМОЖЕТЕ ИЗМЕНИТЬ ВАШИ ОТВЕТЫ.',
    }
}

# Функция для получения текущего языка пользователя
async def get_user_language(telegram_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{BACKEND_URL}/get_user_language', json={'telegram_id': str(telegram_id)}) as resp:
            if resp.status == 200:
                return await resp.json()
            return None
async def set_user_language(telegram_id, language):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BACKEND_URL}/set_user_language', json={'telegram_id': str(telegram_id), 'lang': language}) as resp:
            if resp.status == 200:
                return await resp.json()
            return None


# Функция для отправки переведенного сообщения
async def send_translated_message(message: types.Message, state: FSMContext, key: str, callback_user_id: int = None, **kwargs):
    if callback_user_id:
        lang = await get_user_language(callback_user_id)
    else:
        lang = await get_user_language(message.from_user.id)
    text = translations[lang][key].format(**kwargs)
    await message.reply(text)

executor = ThreadPoolExecutor()

async def download_audio_file(file_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            return await response.read()

async def convert_ogg_to_wav(audio_content):
    audio = await asyncio.get_event_loop().run_in_executor(executor, AudioSegment.from_ogg, io.BytesIO(audio_content))
    # Конвертируем аудио в моно, 16-bit, 16kHz
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio_wav = io.BytesIO()
    await asyncio.get_event_loop().run_in_executor(executor, audio.export, audio_wav, 'wav')
    audio_wav.seek(0)
    return audio_wav

@dp.message(Command("select_language"))
async def select_language(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="English", callback_data="lang_en"),
        InlineKeyboardButton(text="Русский", callback_data="lang_ru")]
    ])
    await message.reply(translations['en']['select_language_prompt'], reply_markup=keyboard)
    await state.set_state(Form.waiting_for_language_selection)

@dp.callback_query(Form.waiting_for_language_selection)
async def process_language_selection(callback_query: types.CallbackQuery, state: FSMContext):
    selected_language = callback_query.data.split('_')[-1]
    await set_user_language(callback_query.from_user.id, selected_language)
    await state.update_data(language=selected_language)
    await send_translated_message(callback_query.message, state, 'language_selected', callback_user_id=callback_query.from_user.id)
    await callback_query.answer()
    await state.clear()

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.from_user.full_name
    if await start_user_registration(user_id, name):
        await send_translated_message(message, state, 'welcome')
    else:
        await send_translated_message(message, state, 'registration_failed')

@dp.message(Command("select_company"))
async def select_company(message: types.Message, state: FSMContext):
    await send_translated_message(message, state, 'select_company')
    await state.set_state(Form.waiting_for_company_name)

@dp.message(Form.waiting_for_company_name)
async def process_company_name(message: types.Message, state: FSMContext):
    company_name = message.text
    result = await check_backend('check_company', {'name': company_name})
    if result and result['exists']:
        resp = await add_user_to_company(message.from_user.id, company_name)
        if resp:
            await state.update_data(company_selected=True)
            await send_translated_message(message, state, 'company_exists')
            await state.clear()
        else:
            await message.reply("Failed to add user to company. Please try again.")

    else:
        await send_translated_message(message, state, 'company_not_exist')
        await state.set_state(Form.waiting_for_company_name)

@dp.message(Command("select_vacancy"))
async def select_job(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)

    if data['result_score'] is not None:
        await send_translated_message(message, state, 'interview_finished')
        return
    if not data or not data.get('company_name'):
        await send_translated_message(message, state, 'select_company_first')
        return


    await send_translated_message(message, state, 'provide_job_title')
    await state.set_state(Form.waiting_for_job_title)

@dp.message(Form.waiting_for_job_title)
async def process_job_title(message: types.Message, state: FSMContext):
    job_title = message.text
    data = await get_backend_data(message.from_user.id)
    result = await check_backend('check_job', {'name': job_title, 'company_name': data['company_name']})
    if result and result['exists']:
        resp = await add_user_to_job(
            {'telegram_id': str(message.from_user.id), 'job': job_title, 'company_name': data['company_name']})
        if resp:
            await state.update_data(job_selected=True)
            await send_translated_message(message, state, 'job_exists')
            await state.clear()
        else:
            await send_translated_message(message, state, 'job_not_exist')
            await state.set_state(Form.waiting_for_job_title)
    else:
        await send_translated_message(message, state, 'job_not_exist')
        await state.set_state(Form.waiting_for_job_title)

@dp.message(Command("score_resume"))
async def check_resume(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)
    job = data.get('job_name')
    if data['result_score'] is not None:
        await send_translated_message(message, state, 'interview_finished')
        return
    if not data or not job:
        await send_translated_message(message, state, 'select_job_first')
        return

    await send_translated_message(message, state, 'resume_prompt')
    await state.set_state(Form.waiting_for_resume)

@dp.message(Form.waiting_for_resume)
async def process_resume(message: types.Message, state: FSMContext):
    if not message.document:
        await send_translated_message(message, state, 'resume_invalid')
        return

    document = message.document
    file_id = document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_path}'
    data = await get_backend_data(message.from_user.id)

    content = requests.get(file_url).text
    result = await score_resume_request(content=content, user_id=message.from_user.id)
    if result:
        await state.update_data(resume_checked=True)
        await send_translated_message(message, state, 'resume_valid')
        await state.clear()
    else:
        await send_translated_message(message, state, 'resume_invalid')
        await state.set_state(Form.waiting_for_resume)

@dp.message(Command("check_hardskills"))
async def check_hardskills(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)

    req_data = {'name': data.get('job_name'), 'company_name': data.get('company_name')}
    requirements = await get_requirements_request(req_data)
    requirements = requirements['requirements']
    if data['result_score'] is not None:
        await send_translated_message(message, state, 'interview_finished')
        return
    if not data or not data.get('resume_score'):
        await send_translated_message(message, state, 'check_resume_first')
        return
    await state.update_data(current_question=0, total_questions=1, previous_questions="", requirements=requirements,
                            last_answer='', last_question='', results_sum=0)
    await state.set_state(Form.waiting_for_hardskill_answer)
    previous_questions = ''
    lang = await get_user_language(message.from_user.id)
    first_question, first_answer = create_question_with_answer(previous_questions, requirements, lang)
    await send_translated_message(message, state, 'hardskills_prompt')
    await message.reply(first_question)
    await state.update_data(last_answer=first_answer, last_question=first_question)

# Обработка ответов на вопросы

# Укажите путь к скачанной модели Vosk Big 0.42
model_dict = {
    'ru': STT('vosk-model-ru-0.42'),
    'en': STT('vosk-model-en-us-0.22')
}
@dp.message(Form.waiting_for_hardskill_answer)
async def process_hardskill_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_question = data['current_question']
    total_questions = data['total_questions']
    previous_questions = data['previous_questions']
    requirements = data['requirements']
    correct_answer = data['last_answer']
    last_question = data['last_question']
    results_sum = data['results_sum']

    if message.voice:  # Если сообщение содержит аудиофайл
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_path}'
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_on_disk = Path("", f"{file_id}.tmp")
        await bot.download_file(file_path, destination=file_on_disk)
        user_answer = model_dict[await get_user_language(message.from_user.id)].audio_to_text(file_on_disk)

    else:
        user_answer = message.text

    comparison_result = compare_answers(user_answer, correct_answer, await get_user_language(message.from_user.id))
    results_sum += comparison_result

    await send_translated_message(message, state, 'answer_accepted')

    if current_question + 1 < total_questions:
        next_question, next_answer = create_question_with_answer(previous_questions, requirements, await get_user_language(message.from_user.id))
        await send_translated_message(message, state, 'next_question')
        await message.reply(next_question)
        await state.update_data(current_question=current_question + 1,
                                previous_questions=previous_questions + f"Вопрос: {last_question}\nОтвет: {user_answer}\n\n",
                                last_answer=user_answer, last_question=next_question, results_sum=results_sum)
        await state.set_state(Form.waiting_for_hardskill_answer)
    else:
        resp = requests.post(f'{BACKEND_URL}/update_hardskills_score',
                             json={'telegram_id': str(message.from_user.id), 'score': results_sum})
        if resp.status_code == 200:
            await state.update_data(hardskills_checked=True)
            await send_translated_message(message, state, 'skills_assessment_complete')
            await state.clear()
        else:
            await send_translated_message(message, state, 'finalize_failed')
            await state.clear()

@dp.message(Command("check_softskills"))
async def check_softskills(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)
    print(data)

    if data['result_score'] is not None:
        await send_translated_message(message, state, 'interview_finished')
        return
    if not data or not data.get('hard_skills_score'):
        await send_translated_message(message, state, 'check_hardskills_first')
        return

    link = await start_dnd_game(message.from_user.id)
    await state.update_data(softskills_checked=True)
    await send_translated_message(message, state, 'softskills_prompt')
    await message.reply(link)
    await send_translated_message(message, state, 'finalize_warning')

@dp.message(Command("finalize"))
async def finalize(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)
    if data['result_score'] is not None:
        await send_translated_message(message, state, 'interview_finished')
        return
    if data['soft_skills_score'] is not None:
        result  = await finalize_interview(message.from_user.id)
        if result:
            await send_translated_message(message, state, 'finalize_success')
        else:
            await send_translated_message(message, state, 'finalize_failed')
    else:
        await send_translated_message(message, state, 'finalize_prompt')

if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)
