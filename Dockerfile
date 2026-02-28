FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY req.txt ./
RUN pip install --no-cache-dir -r req.txt

COPY src ./src
COPY src/IPSA_MODEL ./src/IPSA_MODEL
COPY code_formatter.py ./code_formatter.py
COPY images ./images

ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py"]
