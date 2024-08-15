import logging
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

API_TOKEN = '7316928282:AAEw4DLPo6cAwMgFQ1fIcBPuw550qZj-2us'
BACKEND_URL = 'http://localhost:8000'

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Определение состояний
class Form(StatesGroup):
    waiting_for_company_name = State()
    waiting_for_job_title = State()
    waiting_for_resume = State()
    waiting_for_hardskill_answer = State()
    waiting_for_softskills_check = State()

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

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.from_user.full_name
    if await start_user_registration(user_id, name):
        await message.reply("Welcome! You have been registered.")
    else:
        await message.reply("Registration failed. Please try again later.")

@dp.message(Command("select_company"))
async def select_company(message: types.Message, state: FSMContext):
    await message.reply("Please write company name to bot.")
    await state.set_state(Form.waiting_for_company_name)

@dp.message(Form.waiting_for_company_name)
async def process_company_name(message: types.Message, state: FSMContext):
    company_name = message.text
    result = await check_backend('check_company', {'name': company_name})
    if result and result['exists']:
        resp = await add_user_to_company(message.from_user.id, company_name)
        if resp:
            await state.update_data(company_selected=True)
            await message.reply("Company exists and is selected.")
            await state.clear()
        else:
            await message.reply("Failed to add user to company. Please try again.")

    else:
        await message.reply("Company does not exist. Try again or type /select_company to start over.")
        await state.set_state(Form.waiting_for_company_name)

@dp.message(Command("select_vacancy"))
async def select_job(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)
    if not data or not data.get('company_name'):
        await message.reply("Please select a company first using /select_company.")
        return

    await message.reply("Please provide a job title.")
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
            await message.reply("Job exists and is selected.")
            await state.clear()
        else:
            await message.reply("Failed to add user to the job. Try again or type /select_vacancy to start over.")
            await state.set_state(Form.waiting_for_job_title)
    else:
        await message.reply("Job does not exist. Try again or type /select_vacancy to start over.")
        await state.set_state(Form.waiting_for_job_title)

@dp.message(Command("score_resume"))
async def check_resume(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)
    job = data.get('job_name')
    print(data)
    if not data or not job:
        await message.reply("Please select a job first using /select_vacancy.")
        return

    await message.reply("Please reply to this message with your resume file.")
    await state.set_state(Form.waiting_for_resume)

@dp.message(Form.waiting_for_resume)
async def process_resume(message: types.Message, state: FSMContext):
    if not message.document:
        await message.reply("Please provide a resume file.")
        return

    document = message.document
    file_id = document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_path}'
    data = await get_backend_data(message.from_user.id)

    content = requests.get(file_url).text
    print(type(content))
    result = await score_resume_request(content=content, user_id=message.from_user.id)
    print(result)
    if result:
        await state.update_data(resume_checked=True)
        await message.reply("Resume is valid and checked.")
        await state.clear()
    else:
        await message.reply("Resume is not valid. Please try again.")
        await state.set_state(Form.waiting_for_resume)

@dp.message(Command("check_hardskills"))
async def check_hardskills(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)

    req_data = {'name': data.get('job_name'), 'company_name': data.get('company_name')}
    requirements = await get_requirements_request(req_data)
    requirements = requirements['requirements']
    if not data or not data.get('resume_score'):
        await message.reply("Please check your resume first using /check_resume.")
        return
    await state.update_data(current_question=0, total_questions=10, previous_questions="", requirements=requirements,
                            last_answer='', last_question='', results_sum=0)
    await state.set_state(Form.waiting_for_hardskill_answer)
    previous_questions = ''
    first_question, first_answer = create_question_with_answer(previous_questions, requirements)
    await message.reply(f"Starting hard skills assessment. Answer the following question:\n\n{first_question}")
    await state.update_data(last_answer=first_answer, last_question=first_question)

# Обработка ответов на вопросы
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



    user_answer = message.text

    comparison_result = compare_answers(user_answer, correct_answer)
    results_sum += comparison_result

    await message.reply("Your answer is accepted.")

    if current_question + 1 < total_questions:
        next_question, next_answer = create_question_with_answer(previous_questions, requirements)
        await message.reply(f"Next question:\n\n{next_question}")
        await state.update_data(current_question=current_question + 1, previous_questions=previous_questions + f"Question: {last_question}\nAnswer: {user_answer}\n\n", last_answer=user_answer, last_question=next_question, results_sum=results_sum)
        await state.set_state(Form.waiting_for_hardskill_answer)
    else:
        resp = requests.post(f'{BACKEND_URL}/update_hardskills_score', json={'telegram_id': str(message.from_user.id), 'result': results_sum})
        if resp.status_code == 200:
            await state.update_data(hardskills_checked=True)
            await message.reply("Hard skills assessment completed.")
            await state.clear()
        else:
            await message.reply("Failed to update hard skills score. Please try again.")
            await state.clear()

# Примерные реализации функций generate_question, generate_answer и compare_answers

@dp.message(Command("check_softskills"))
async def check_softskills(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)
    if not data or not data.get('hardskills_checked'):
        await message.reply("Please check your hard skills first using /check_hardskills.")
        return

    softskills_score = random.random()
    await state.update_data(softskills_checked=True)
    await message.reply(f"Soft skills assessment completed. Score: {softskills_score:.2f}")

@dp.message(Command("finalize"))
async def finalize(message: types.Message, state: FSMContext):
    data = await get_backend_data(message.from_user.id)
    if all(key in data for key in ['company_selected', 'job_selected', 'resume_checked', 'hardskills_checked', 'softskills_checked']):
        result = await check_backend('finalize', {'telegram': message.from_user.id})
        if result and result['finalized']:
            await message.reply("Interview process finalized successfully.")
        else:
            await message.reply("Failed to finalize the interview process.")
    else:
        await message.reply("Please complete all previous steps before finalizing.")

if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)
