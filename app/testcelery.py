from flask import Flask
from celery import Celery
import time

app = Flask(__name__)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Define a Celery task
@celery.task
def long_task():
    time.sleep(5)
    return "Task completed!"

@app.route('/')
def index():
    long_task.apply_async()
    return "Task started in the background!"

if __name__ == '__main__':
    app.run(debug=True)
