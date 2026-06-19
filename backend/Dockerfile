# Берем официальный легкий образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости для работы с PostgreSQL
RUN apt-get update && apt-get install -y gcc libpq-dev && apt-get clean

# Указываем рабочую папку внутри контейнера
WORKDIR /app

# Копируем список зависимостей
COPY requirements.txt /app/

# Обновляем pip и устанавливаем библиотеки
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта в контейнер
COPY . /app/

# Открываем стандартный порт Django наружу
EXPOSE 8000

# Команда для автоматического запуска сервера при старте контейнера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
