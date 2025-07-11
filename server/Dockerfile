FROM python:3.10-slim

WORKDIR /tmp/demo

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 3003

HEALTHCHECK CMD curl --fail http://localhost:3003/_stcore/health

# python3.10 main.py
ENTRYPOINT ["python", "main.py"]