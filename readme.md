# IndPro

Проект представляет собой API для работы с заявками и пользователями, реализованное на FastAPI.

## Структура

- `main.py` — приложение FastAPI и подключение маршрутов.
- `userslogic_controller.py` — регистрация, проверка email и авторизация.
- `bids_controller.py` — CRUD для заявок с авторизацией и проверкой email-подтверждения.
- `token_driver.py` — генерация и проверка JWT.
- `emailtool.py` — отправка кода подтверждения на email.
- `db.py` — подключение к базе данных и схема таблиц.
- `tables.sql` — SQL-схема базы данных.

## Установка и запуск

1. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r reqs.txt
```

2. Создайте `.env` файл и задайте переменные:

```env
JWT_KEY=your_secret_key
EMAIL=your_email@example.com
EMAIL_PASSWORD=your_email_password
PG_HOST=localhost
PG_PORT=5432
PG_DBNAME=your_database
PG_USER=your_user
PG_PASSWORD=your_password
```

3. Запустите приложение:

```bash
uvicorn main:app --reload
```

### Запуск через Docker

В проекте есть `Dockerfile` и `docker-compose.yml`, поэтому можно поднять сервисы через Docker Compose.

```bash
docker compose up --build
```

Сервис `app` будет доступен на `http://localhost:8000`.

В `docker-compose.yml` уже заданы переменные для PostgreSQL и приложения:
- `PG_HOST=db`
- `PG_PORT=5432`
- `PG_DBNAME=myip`
- `PG_USER=postgres`
- `PG_PASSWORD=mysecretpassword`
- `JWT_KEY` и `EMAIL`/`EMAIL_PASSWORD`

PostgreSQL будет слушать на порту `2588` хоста, но приложение подключается к контейнеру `db` по имени сервиса.

## API

### 1. Регистрация пользователя

`POST /api/users/register`

Тело запроса (JSON):

```json
{
  "username": "user",
  "password": "password",
  "fio": "Фамилия Имя Отчество",
  "job": "Должность",
  "email": "email@example.com"
}
```

Ответ:

- `200` — регистрация прошла, код подтверждения отправлен на email.
- `500` — ошибка при сохранении данных.

### 2. Подтверждение email

`GET /api/users/verify/{code}`

- Если код существовал и email не был подтверждён — помечает пользователя как `is_verified = TRUE`.
- Если код не найден — возвращается `404`.
- Если email уже подтверждён — возвращает `200` с сообщением.

### 3. Авторизация

`POST /api/users/auth`

Тело запроса (JSON):

```json
{
  "username": "user",
  "password": "password"
}
```

Ответы:

- `200` — возвращает JWT.
- `401` — неверные данные.

## Защищённые маршруты заявок

Для всех операций с заявками требуется заголовок `Authorization: Bearer <token>`.

### 4. Создание заявки

`POST /api/bids/createnew`

Формы:
- `name` — заголовок заявки
- `content` — основной текст
- `add_content` — дополнительный текст
- `files` — список файлов

Токен проверяется, а также дополнительно проверяется, что пользователь подтверждён (`is_verified = TRUE`).

Ответы:

- `200` — заявка создана.
- `401` — токен недействителен, просрочен или email не подтверждён.
- `500` — серверная ошибка.

### 5. Получение одной заявки

`GET /api/bids/getone?id=<id>`

Проверяется токен и права доступа:
- пользователь должен быть админом или владельцем заявки.

Ответы:

- `200` — возвращает данные заявки.
- `403` — нет доступа.
- `404` — заявка не найдена.

### 6. Получение всех заявок

`GET /api/bids/getall`

Доступно только админам.

### 7. Изменение статуса заявки

`PATCH /api/bids/changestat`

Тело запроса:

```json
{
  "id": "<bid_id>",
  "status": "new status"
}
```

Доступно только админам.

### 8. Удаление заявки

`DELETE /api/bids/deleteone?id=<id>`

Доступно только админам.

## Токены и авторизация

- Токены создаются в `token_driver.py`.
- В JWT помещаются поля `id` и `passhash` пользователя.
- Проверка токена возвращает:
  - `payload` — если токен действителен;
  - `"Token Expired"` — если срок жизни истёк;
  - `None` — если токен неверный.

## База данных

Таблица `users` содержит:
- `username`
- `passhash`
- `fio`
- `email`
- `job`
- `verify_code`
- `is_verified`

Таблица `bids` содержит:
- `name`
- `content`
- `owner_id`
- `owner_username`
- `owner_fio`
- `owner_job`
- `files`
- `status`

## Примечания

- Обязательно задавать переменные окружения через `.env`.
- В коде используется явная обработка `HTTPException`, чтобы фронт получал корректный статус и `detail`.
- Логика `verify_email` проверяет, что код существует, и возвращает понятный ответ, если email уже подтверждён.
