from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired

class Generateform(FlaskForm):
    id = IntegerField('tempid')

class OpenAiform(FlaskForm):
    key = StringField('Stripe Api Key', validators=[DataRequired()])
    product_id = StringField('Product Id', validators=[DataRequired()])
    endpoint_secret = StringField('Endpoint Secret', validators=[DataRequired()])
    openai_key = StringField('Open Api Key')

class CourseForm(FlaskForm):
    type = SelectField('Course Type', choices=[('1', 'Daily'), ('2', 'Single')], validators=[DataRequired()])
    name = StringField('Course Title', validators=[DataRequired()])
