FROM python:3.11-slim

WORKDIR /app

COPY ../app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../app /app
COPY ../html /app/templates
COPY ../static /app/static

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "crawler_predictor_site:app"]
