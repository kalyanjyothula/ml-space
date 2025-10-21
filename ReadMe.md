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

* <img width="1450" height="785" alt="Screenshot 2025-10-21 at 1 47 00 PM" src="https://github.com/user-attachments/assets/fd3876de-65f0-4c02-be4b-6a6d40250f91" />
<img width="1450" height="262" alt="Screenshot 2025-10-21 at 1 47 19 PM" src="https://github.com/user-attachments/assets/6f0147c8-ac8b-498d-86ed-1395aa4bc797" />


