FROM python:3.11-slim

WORKDIR /tmp/demo

COPY requirements.txt requirements.txt

# Install system dependencies for OpenCV and image/PDF processing
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 3003

HEALTHCHECK CMD curl --fail http://localhost:3003/_stcore/health

ENTRYPOINT ["python", "main.py"]