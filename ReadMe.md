### created and activate py environment
* conda create -n flask-api-env python=3.12 -y && conda activate flask-api-env

### install packages using requirement.txt
* pip install -r requirements.txt

### To check the activated venv
* which python

### To run the application
* unicorn --bind 0.0.0.0:8000 wsgi:app

### Swagger UI
* http://127.0.0.1:8000/swagger
