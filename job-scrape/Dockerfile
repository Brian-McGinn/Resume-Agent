FROM python:3.10-slim

RUN pip install -U python-jobspy mcp

WORKDIR /src

COPY jobs.py jobs.py

ENTRYPOINT ["python", "jobs.py"]