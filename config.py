import os
from datetime import timedelta
from sqlalchemy.pool import QueuePool

class Config:
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SECRET_KEY = 'your_secret_key_here'
    SECURITY_PASSWORD_SALT = 'wwrdvsdg547547547r5744t'
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False  # Set to False to use 'PERMANENT_SESSION_LIFETIME'
    SQLALCHEMY_DATABASE_URI = 'mysql://g304975_testuser:rzYT=HEmyVX+@localhost/g304975_nyxmediatest'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 28000
    SQLALCHEMY_POOL_SIZE = 90      # Number of connections in the pool
    SQLALCHEMY_POOL_TIMEOUT = 200  # Timeout (in seconds) to wait for a connection from the pool
    RECAPTCHA_PUBLIC_KEY = 'your-recaptcha-public-key'
    RECAPTCHA_PRIVATE_KEY = 'your-recaptcha-private-key'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  
        'poolclass': QueuePool
    }

    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/attachment')
    MAIL_USERNAME = 'info@nyxmedia.es'  # Replace with your email
    MAIL_PASSWORD = 'Faustino69!'  # Replace with your email password
    MAIL_DEFAULT_SENDER = 'info@nyxmedia.es'
    MAIL_SERVER = 'mail.nyxmedia.es'  # Your SMTP server
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    # Celery configuration
    REDIS_URL = 'redis://localhost:6379/0'

    # Session Lifetime Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Set session lifetime to 7 days
