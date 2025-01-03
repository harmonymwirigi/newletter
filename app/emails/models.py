from app import db
from flask_login import UserMixin
from datetime import datetime

class EmailTemplate(db.Model, UserMixin):
    __tablename__ = 'email_templates'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    header = db.Column(db.String(255), nullable=True)
    body = db.Column(db.Text, nullable=False)
    footer = db.Column(db.Text, nullable=False)
    compaign = db.Column(db.Integer, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('adminuser.id'))

    # Relationship to GeneratedEmail; no need to specify lazy loading here again in backref
    generated_emails = db.relationship('GeneratedEmail', back_populates='email_template')

    def __repr__(self):
        return f"<EmailTemplate(id='{self.id}', header='{self.header}')>"
class GeneratedEmail(db.Model):
    __tablename__ = 'generated_emails'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    header = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)
    footer = db.Column(db.Text, nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_sent = db.Column(db.Boolean, default=False)  # Indicates if the email is sent
    # New column to store conversation history in JSON format
    conversation = db.Column(db.Text, nullable=True)  # Stores the conversation JSON string

    # Define relationship with EmailTemplate model
    email_template = db.relationship('EmailTemplate', back_populates='generated_emails')

    def __repr__(self):
        return f"<GeneratedEmail(id='{self.id}', template_id='{self.template_id}', is_sent='{self.is_sent}')>"

