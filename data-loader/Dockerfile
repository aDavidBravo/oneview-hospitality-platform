FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pandas==2.2.2 \
    numpy==1.26.4 \
    faker==24.4.0 \
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.29

COPY . .

CMD ["python", "generate_all.py"]
