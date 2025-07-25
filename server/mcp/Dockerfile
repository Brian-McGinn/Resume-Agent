FROM python:3.11-slim

WORKDIR /mcp-server

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3004

ENTRYPOINT ["python", "mcp_server.py"]