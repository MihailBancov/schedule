FROM python:3.12-slim
WORKDIR /app
COPY orar.py bot.py i18n.py schedule_data.json requirements.txt ./
CMD ["python", "bot.py"]
