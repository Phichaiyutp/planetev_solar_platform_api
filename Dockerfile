FROM python:3.12

WORKDIR /code

COPY requirements.txt .
COPY .env .

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "5000"]
