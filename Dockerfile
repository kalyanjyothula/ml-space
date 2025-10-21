FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

# Use Gunicorn for production serving
CMD ["gunicorn", "--reload", "--bind", "0.0.0.0:8000", "wsgi:app", "--timeout", "120"]
