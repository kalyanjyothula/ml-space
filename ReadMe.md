### created and activate py environment
* conda create -n flask-api-env python=3.12 -y && conda activate flask-api-env

### install packages using requirement.txt
* pip install -r requirements.txt

### To check the activated venv
* which python

### To run the application
* gunicorn --bind 0.0.0.0:8000 wsgi:app
* (or) gunicorn --reload --bind 0.0.0.0:8000 wsgi:app

### To run redis
* brew services start redis

### to test redis connection
* redis-cli ping

### To stop redis server in mac
* brew services stop redis

### Swagger UI
* http://127.0.0.1:8000/swagger
