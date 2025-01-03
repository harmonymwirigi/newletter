from werkzeug.security import check_password_hash
from app import db  # Import the db instance from app/__init__.py
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from enum import Enum


class AdminRole(Enum):
    ADMIN = 'Admin'
    SUPER_ADMIN = 'Super Admin'

class Adminuser(db.Model):
    __tablename__ = 'adminuser'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=True)
    course = db.relationship('app.course.model.Course')
    template = db.relationship('app.emails.models.EmailTemplate')
    password = db.Column(db.String(128), nullable=True)
    currency = db.Column(db.String(128), default="USD")
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum(AdminRole), default=AdminRole.ADMIN, nullable=False)
    stripe_account_id = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return str(self.id)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id
    # Method to generate verification token
    # Method to generate verification token
    def generate_verification_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt=current_app.config['SECURITY_PASSWORD_SALT'])

    # Static method to verify the token
    @staticmethod
    def verify_verification_token(token, expiration=3600):  # Add expiration as parameter
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
        except:
            return None
        return Adminuser.query.get(data['user_id'])

class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    customer_id = db.Column(db.String(200), nullable=True)
    payment_intent_id = db.Column(db.String(200), nullable=True)
    amount = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Integer, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    unsubsciption_reason = db.Column(db.String(2000), nullable=True)
    

    def check_password(self, password):
        return check_password_hash(self.password)

    def __repr__(self):
        return str(self.id)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id
