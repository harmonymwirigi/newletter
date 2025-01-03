from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, ColorField, IntegerField, FileField, SelectField, HiddenField, DecimalField, BooleanField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

class Customizeform(FlaskForm):
    title = StringField('Title')
    color = ColorField('Color')
    price = DecimalField('Price')
    free = BooleanField('Is this course free?', default=False)
    link = StringField("Course Link")
    currency = SelectField('Currency', choices=[('usd', 'USD'), ('eur', 'EUR')], validators=[DataRequired()])

class DeleteResource(FlaskForm):
    id = IntegerField("hide")

class CourseResourcesForm(FlaskForm):
    title = StringField('Title')
    course_description = TextAreaField('Course Description', validators=[])
    advert = FileField('Advert (Video or Photo)', validators=[])
    position = SelectField('Position', choices=[('top', 'TOP'), ('bottom', 'Bottom')], validators=[DataRequired()])

class Emailform(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    header = TextAreaField('Header', validators=[DataRequired()])
    body = CKEditorField('Body', validators=[DataRequired()])  # Use CKEditorField for the body
    footer = TextAreaField('Footer', validators=[DataRequired()])
    attachment = FileField('Attachment')
