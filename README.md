# tyler_durden_bot
Бот для "Настольного клуба"

Инструкция. Внешний вид ридми приведу в порядок чуть позже.

1. Создаём ВО, запускаем его, устанавливаем зависимости, создаём .env по подобию .env.example
-python -m venv venv
-. venv/scripts/activate
-pip install -r requirements.txt

2. Запускаем код, чтобы создалась БД, затем останавливаем
-python main.py

3. Подключаемся к БД
-psql -U postgres
вводим пароль
-CREATE DATABASE tyler_durden_db;
-CREATE USER bot_user WITH PASSWORD 'password';
-GRANT ALL PRIVILEGES ON DATABASE tyler_durden_db TO bot_user;
-GRANT ALL PRIVILEGES ON SCHEMA public TO bot_user;
-GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bot_user;

4. Запускаем код, пользуемся функционалом (или его отсутствием на данный момент)
-python main.py