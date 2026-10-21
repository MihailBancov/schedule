FROM python:3.12-slim
WORKDIR /app
COPY orar.py bot.py requirements.txt ./
CMD ["python", "bot.py"]
