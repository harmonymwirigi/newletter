# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
import yagmail
from flask_mail import Mail
from config import Config
from flask_ckeditor import CKEditor
from redis import Redis
from rq import Queue
import os
from flask_cors import CORS




# Initialize Flask extensions
db = SQLAlchemy()
mail = Mail()
admin = Admin()
migrate = Migrate()
cache = Cache(config={'CACHE_TYPE': 'simple'})
login_manager = LoginManager()
ckeditor = CKEditor()

# Redis configuration for RQ
redis = Redis.from_url(Config.REDIS_URL)
task_queue = Queue(connection=redis)
app = Flask(__name__)
# Function to initialize yagmail
def init_yagmail(app):
    yag = yagmail.SMTP(
        user=app.config['MAIL_USERNAME'],
        password=app.config['MAIL_PASSWORD'],
        host=app.config['MAIL_SERVER']
    )
    return yag

def create_app():
    
    app.config.from_object(Config)
    
    # Initialize extensions
    mail.init_app(app)
    db.init_app(app)
    admin.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    CORS(app)
    # Initialize yagmail
    app.yag = init_yagmail(app)

    # User loader function required by Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.auth.model import Adminuser
        return Adminuser.query.filter_by(id=user_id).first()

    # Register Blueprints
    from app.auth.route import auth_bp
    from app.user.route import user_bp
    from app.course.route import courses

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(courses, url_prefix='/compaign')

    # Initialize Flask extensions within app context
    with app.app_context():
        from app.auth.model import User, Adminuser
        from app.course.model import Course
        from app.emails.models import EmailTemplate
        
        db.create_all()  # Create database tables for our models
    
        
    return app


