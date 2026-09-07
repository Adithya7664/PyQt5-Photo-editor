FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

COPY styles/ styles/
COPY api/ api/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]