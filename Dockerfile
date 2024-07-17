FROM python:3.12
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
COPY ./.env /code/.env
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "5000"]