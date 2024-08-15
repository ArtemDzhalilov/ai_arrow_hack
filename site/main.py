import streamlit as st
import requests
import pandas as pd
# Укажите URL вашего FastAPI backend
API_URL = "http://localhost:8000"

# Инициализация сессий
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'company_name' not in st.session_state:
    st.session_state['company_name'] = None

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Вход"

# Функция для смены страницы


# Страница логина
def login_page():
    st.header("Вход")
    username = st.text_input("Login", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        response = requests.post(f"{API_URL}/login", data={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            st.session_state['logged_in'] = True
            st.session_state['company_name'] = response.json().get("company_name")
            st.success(f"Добро пожаловать, {username}!")
            st.session_state['current_page'] = "Dashboard"
        else:
            st.error(response.json().get("detail", "Неверный логин или пароль"))

# Страница регистрации
def registration_page():
    st.header("Регистрация")
    username = st.text_input("Login", key="reg_username")
    password = st.text_input("Password", type="password", key="reg_password")
    company_name = st.text_input("Company Name", key="reg_company_name")
    if st.button("Register"):
        response = requests.post(f"{API_URL}/register", json={
            "username": username,
            "password": password,
            "company_name": company_name
        })
        if response.status_code == 200:
            st.success("Регистрация успешна!")
            st.session_state['current_page'] = "Вход"
        else:
            st.error(response.json().get("detail", "Ошибка регистрации"))

# Страница управления
def dashboard_page():
    st.header("Управление")

    option = st.selectbox("Выберите действие", [
        "Создание вакансии",
        "Удаление вакансии",
        "Инфо"
    ])

    if option == "Создание вакансии":
        create_job_page()
    elif option == "Удаление вакансии":
        delete_job_page()
    elif option == "Инфо":
        info_page()

# Страница загрузки файла

# Страница создания вакансии
def create_job_page():
    st.subheader("Создание вакансии")
    job_name = st.text_input("Job Name")
    uploaded_file = st.file_uploader("Job requirements", type="txt")
    if st.button("Create Job"):
        response = requests.post(f"{API_URL}/create_job", json={
            "name": job_name,
            "file": uploaded_file.read().decode("utf-8"),
            "company_name": st.session_state['company_name']
        })
        if response.status_code!=200:
            st.error("Ошибка создания вакансии")
        response = requests.post(f"{API_URL}/create_file", json={
            'content': uploaded_file.getvalue().decode("utf-8"),
            'company_name': st.session_state['company_name'],
            'job_name': job_name
        })
        if response.status_code == 200:
            st.success("Файл загружен успешно!")
        else:
            st.error("Ошибка загрузки файла")

# Страница удаления вакансии
def delete_job_page():
    st.subheader("Удаление вакансии")
    job_names = requests.get(f"{API_URL}/get_jobs_by_company_name", json={"name": st.session_state['company_name']}).json()
    try:
        job_names = [job["name"] for job in job_names]
        job_name = st.selectbox("Выберите вакансию для удаления", job_names)
        if st.button("Delete Job"):
            response = requests.delete(f"{API_URL}/delete_job", json={
                "name": job_name,
                "company_name": st.session_state['company_name']
            })
            if response.status_code == 200:
                st.success("Вакансия удалена успешно!")
            else:
                st.error("Ошибка удаления вакансии")
    except:
        st.text("Нет вакансий для удаления")

# Страница регистрации кандидата


# Страница получения вакансий
def info_page():
    st.subheader("Информация о кандидатах")
    try:
        response = requests.get(f"{API_URL}/get_jobs_by_company_name", json={"name": st.session_state['company_name']})
        if response.status_code == 200:
            jobs = response.json()
        else:
            jobs = []

        all_candidates = []

        for job in jobs:
            response = requests.get(f"{API_URL}/get_candidates_by_job_name", json=job)
            if response.status_code == 200:
                candidates = response.json()
                for candidate in candidates:
                    candidate['job_name'] = job['name']
                all_candidates.extend(candidates)
            else:
                st.error(f"Ошибка получения кандидатов для вакансии {job['name']}")

        if all_candidates:
            print(all_candidates)
            # Преобразование данных в DataFrame
            df = pd.DataFrame(all_candidates)

            # Заполнение None значений в колонке 'score' для корректной сортировки
            df['result_score'] = df['result_score'].apply(lambda x: x if x is not None else float('-inf'))

            # Сортировка по итоговому скору (по убыванию)
            df = df.sort_values(by='result_score', ascending=False)

            # Замена '-inf' обратно на None для отображения
            df['result_score'] = df['result_score'].apply(lambda x: x if x != float('-inf') else None)
            df.drop(['id', 'company_name'], axis=1, inplace=True)
            desired_order = ['telegram_id', 'user_name', 'job_name', 'resume_score', 'hard_skills_score', 'soft_skills_score', 'result_score']
            existing_columns = [col for col in desired_order if col in df.columns] + [col for col in df.columns if
                                                                                      col not in desired_order]
            df = df[existing_columns]
            # Отображение таблицы
            st.dataframe(df)
        else:
            st.write("Нет кандидатов для отображения")
    except:
        st.text("Нет кандидатов для отображения")

def change_page(page):
    st.session_state['current_page'] = page
# Основная логика приложения
def main():
    st.title("Сайт с регистрацией, входом и управлением данными")

    if not st.session_state['logged_in']:
        page = st.session_state['current_page']
        if page == "Регистрация":
            registration_page()
        elif page == "Вход":
            login_page()
        else:
            st.error("Неверная страница для неавторизованных пользователей")
    else:
        dashboard_page()
    if not st.session_state['logged_in']:
        page = st.sidebar.selectbox(
            "Выберите страницу",
            ["Регистрация", "Вход"],
            index=["Регистрация", "Вход"].index(st.session_state['current_page']),
            key="page_selector",
            on_change=lambda: change_page(st.session_state["page_selector"])
        )

if __name__ == "__main__":
    main()
