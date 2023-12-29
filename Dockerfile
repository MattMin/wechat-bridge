FROM python:3.10-slim

WORKDIR /app

ADD . .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]