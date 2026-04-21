FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    uvicorn[standard]==0.29.0 \
    sqlalchemy==2.0.29 \
    psycopg2-binary==2.9.9 \
    pydantic==2.7.1 \
    scikit-learn==1.4.2 \
    pandas==2.2.2 \
    numpy==1.26.4 \
    joblib==1.4.0 \
    statsmodels==0.14.2
COPY . .
RUN mkdir -p /app/models
EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
