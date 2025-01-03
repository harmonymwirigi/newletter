# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField,TextAreaField,SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField('User Name')
    email = StringField('Dirección de email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[])
    agree_terms = BooleanField('Agree the terms and policy',validators=[DataRequired()])


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class ContactForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Mensaje', validators=[DataRequired()])
    privacy = BooleanField('I have read and accept the privacy policies', validators=[DataRequired()])
    submit = SubmitField('Enviar')
