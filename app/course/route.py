from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.auth.forms import LoginForm, RegistrationForm
from app.auth.model import User, db,Adminuser
from app.course.model import Course,CourseResource
from werkzeug.utils import secure_filename
from app.emails.models import EmailTemplate, GeneratedEmail
from app.emails.forms import Emailstemplate
from app.course.forms import Customizeform, Emailform, CourseResourcesForm, DeleteResource
from app.user.forms import Generateform,OpenAiform, CourseForm
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from flask_mail import Message
from app import mail
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import yagmail
import stripe
from datetime import datetime
import sys
import openai
import requests
import json
from app import create_app
from app import task_queue
from app import app
import json
from flask import jsonify
import redis
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True)
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


courses = Blueprint('courses', __name__)
def retrieve_email_template_from_database(template_id):
    # Query the database to retrieve the email template by ID
    email_template = EmailTemplate.query.filter_by(id=template_id).first()
    return email_template




def send_emails(recipient, subject, template_header, body, footer, user, campaign, attachment_path=None, attachment_filename=None):
    image_url = 'https://nyxmedia.es/static/images/images/67,356x223+66+141/10911913/logo_nyx.png'
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                padding: 20px;
                font-size: 16px;
                line-height: 1.5;
            }}
            .email-container {{
                background-color: #ffffff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }}
            .footer {{
                font-size: 14px;
                color: #fff;
                height: 60px;
                text-align: center;
                background-color: black;
                padding: 20px;
                border-radius: 10px;
            }}
            .footer-content {{
                margin-top: 10px;
            }}
            .footer-content1 {{
                margin-top: 10px;
                color: #fff;
            }}
            .footer a {{
                color: #fff;
                text-decoration: underline;
            }}
            .small-link {{
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <b>Nyxmedia News!</b><br>
            <img src="{image_url}" alt="Logo" height="50" width="50">
            <br>
            <h3>{template_header}</h3>
            <br>
            <p>Es un placer saludarte!</p>
            <div class="header">
                {subject}
            </div>
            <div class="body">
                <p>{body}</p><br>
                <p class="footer-content">{footer}</p>
                <br><br>
                <a href="https://test.nyxmedia.es/unsubscribe/{user}/{campaign}" class="small-link">¿Deseas dejar de recibir nuestras actualizaciones? Haz clic aquí para cancelar tu suscripción.</a>
            </div>
            <br>
            <div class="footer">
                <p class="footer-content1">&copy; 2024 nyxmedia/payments. All rights reserved.</p>
                <p class="footer-content"><a href="mailto:nyxfundation@gmail.com">¿Tienes alguna duda o petición? Haz clic aquí</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = Message(subject=subject, recipients=[recipient], html=html_content)

    if attachment_path and attachment_filename:
        try:
            with open(attachment_path, 'rb') as fp:
                msg.attach(attachment_filename, 'application/octet-stream', fp.read())
        except Exception as e:
            print(f"Failed to attach file: {e}")

    try:
        mail.send(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")



import threading

@courses.route('/<course>', methods=['GET', 'POST'])
@login_required
def dashboard(course):
    customizeform = Customizeform()
    emailform = Emailform()
    tempform = Generateform()
    form = Emailstemplate()
    keyform = OpenAiform()
    compainform = CourseForm()
    email = current_user.email
    ResourcesForm=CourseResourcesForm()
    delete_resource = DeleteResource()

    if form.validate_on_submit():
        # This block will execute when the form is submitted and all fields pass validation
        # Access form data using form.field_name.data
        header = form.Header.data
        body = form.body.data
        footer = form.footer.data

        # Create a new EmailTemplate instance
        email_template = EmailTemplate(header=header, body=body, footer=footer, owner_id=current_user.id, compaign=course)
        # Add the new EmailTemplate instance to the database session
        db.session.add(email_template)
        # Commit the changes to the database
        db.session.commit()
        threading.Thread(target=generate_and_save_emails, args=(email_template.id, course)).start()
        

        return redirect(url_for('courses.dashboard', course=course))  # Redirect to the dashboard to clear the form
    
    # Handle form validation failure as before
    email_templates = EmailTemplate.query.filter_by(owner_id=current_user.id, compaign=course).all()
    courses = Course.query.filter_by(owner_id=current_user.id, status=1).all()
    this_campaign = Course.query.filter_by(id=course).first()
    check_key = this_campaign.stripe_api_key
    color = this_campaign.color or "#fffff"
    code = this_campaign.url
    compaign_id = course
    db.session.commit()

    return render_template('compaigndashboard.html',
                           formu=form,
                           email_templates=email_templates,
                           tempform=tempform,
                           email=email,
                           ResourcesForm=ResourcesForm,
                           keyform=keyform,
                           compainform=compainform,
                           courses=courses,
                           compaign_id=compaign_id,
                           customizeform=customizeform,
                           emailform=emailform,
                           check_key=check_key,
                           url=code,
                           this_campaign=this_campaign,
                           color=color,
                           delete_resource=delete_resource,
                           active_compaign_id=int(course))
                           
@courses.route('/generate_all_emails/<int:course>', methods=['POST'])
@login_required
def generate_all_emails(course):
    """
    Endpoint to handle form submission and initiate email generation.
    """
    form = Emailstemplate()
    if form.validate_on_submit():
        header = form.Header.data
        body = form.body.data
        footer = form.footer.data

        # Create a new EmailTemplate instance
        email_template = EmailTemplate(header=header, body=body, footer=footer, owner_id=current_user.id, compaign=course)
        db.session.add(email_template)
        db.session.commit()

        # Start the email generation in a separate thread
        threading.Thread(target=generate_and_save_emails, args=(email_template.id, course)).start()

        # Return JSON response with template_id
        return jsonify({"message": "Email generation started successfully!", "template_id": email_template.id}), 200
    
    # If form validation fails, return errors as JSON
    errors = {field: form.errors[field] for field in form.errors}
    return jsonify({"errors": errors}), 400


@courses.route('/generate_all_emails_status/<int:template_id>', methods=['GET'])
@login_required
def generate_all_emails_status(template_id):
    """
    Fetch the email generation status from Redis.
    """
    redis_key = f"email_generation_status:{template_id}"
    status = redis_client.get(redis_key)
    
    if status:
        if status.startswith("failed:"):
            error_details = status[len("failed:"):]  # Extract error message
            return jsonify({"status": "failed", "error": error_details}), 200
        return jsonify({"status": status}), 200
    return jsonify({"status": "not_found"}), 404


@courses.route('/email_status/<int:template_id>', methods=['GET'])
@login_required
def email_status(template_id):
    redis_key = f"email_generation_status:{template_id}"
    status = redis_client.get(redis_key)
    if status:
        if status.startswith("failed:"):
            error_details = status[len("failed:"):]  # Extract error message
            return jsonify({"status": "failed", "error": error_details}), 200
        return jsonify({"status": status}), 200
    return jsonify({"status": "not_found"}), 404


# This function will be used to start the background thread

@courses.route('/customize/<campaign>', methods=['POST', 'GET'])
def customize(campaign):
    customizeform = Customizeform()

    if customizeform.validate_on_submit():
        # Extract data from the form
        title = customizeform.title.data
        color = customizeform.color.data
        price = customizeform.price.data
        free = customizeform.free.data
        link = customizeform.link.data
        currency = customizeform.currency.data
        

        # Find the course by ID
        customize = Course.query.filter_by(id=campaign).first()

        if customize:
            # Update the course with the new data
            customize.title = title
            customize.color = color
            customize.price = price
            customize.courselink = link
            customize.currency = currency
            customize.free = free
            

            

            # Commit changes to the database
            db.session.commit()

            return redirect(url_for('courses.dashboard', course=campaign))
        else:
            # Handle the case where the course is not found
            flash('Course not found', 'danger')
            return redirect(url_for('courses.dashboard'))

    # Render the form if validation fails or it's a GET request
    return render_template('customize.html', form=customizeform)
@courses.route('/unsubscribeuser/<int:user_id>/<campaign>', methods=['GET'])
@login_required
def unsubscribeuser(user_id, campaign):
    # Fetch the user object by its id
    user = User.query.filter_by(id=user_id).first()
    resource = Course.query.filter_by(id=campaign).first()
    if user:
        # Update the user's status to 1 (unsubscribed or similar)
        if user.payment_intent_id:
            unsubscribe_user(resource.stripe_api_key, user.payment_intent_id)
        user.status = 1
        db.session.commit()

        # Redirect to the resources page, passing the campaign parameter
        return redirect(url_for('courses.users', id=campaign))

    # If the user is not found, handle the case (optional)
    flash("User not found", "error")
    return redirect(url_for('courses.users', id=campaign))

    

@courses.route('/<campaign>/resources', methods=['POST', 'GET'])
@login_required
def resources(campaign):
    resources = CourseResource.query.filter_by(course=campaign).all()
    compaign_id =campaign
    ResourcesForm = CourseResourcesForm()
    course = Course.query.filter_by(id=campaign).first()
    courses = Course.query.filter_by(owner_id=current_user.id, status=1).all()
    if ResourcesForm.validate_on_submit():
        course_description = ResourcesForm.course_description.data
        advert_file = ResourcesForm.advert.data
        position =  ResourcesForm.position.data
        title = ResourcesForm.title.data
        advert_filename =None
        # Handle the advert file
        if advert_file:
            # Create the directory if it doesn't exist
            advert_dir = 'app/static/adverts'
            if not os.path.exists(advert_dir):
                os.makedirs(advert_dir)

            # Save the advert file
            advert_filename = secure_filename(advert_file.filename)
            advert_path = os.path.join(advert_dir, advert_filename)
            advert_file.save(advert_path)
            
        resource = CourseResource(course= course.id,title = title,position= position,
        course_description = course_description,advert =advert_filename)
        db.session.add(resource)
        db.session.commit()

        return redirect(url_for('courses.resources', campaign=campaign))
        
    customizeform = Customizeform()
    form = Emailstemplate()
    keyform=OpenAiform()
    compainform = CourseForm()
    emailform = Emailform()
    delete_resource = DeleteResource()
    this_campaign = Course.query.filter_by(id=campaign).first()
    return render_template('resources.html', compaign_id=compaign_id,
                            resources= resources,
                            url = this_campaign.url,
                            emailform = emailform,
                            customizeform = customizeform,
                            ResourcesForm = ResourcesForm,
                            formu = form,keyform=keyform,
                            courses=courses,
                            active_compaign_id=int(campaign),
                            delete_resource = delete_resource,
                            compainform = compainform,this_campaign = this_campaign)


@courses.route('/<id>/users')
@login_required
def users(id):
    customizeform = Customizeform()
    form = Emailstemplate()
    keyform=OpenAiform()
    compainform = CourseForm()
    compaign_id =id
    emailform = Emailform()
    delete_resource = DeleteResource()
    ResourcesForm = CourseResourcesForm()
    users =  User.query.filter_by(course_id = id, status =2).all()
    admin_users = Adminuser.query.filter_by(is_verified =True).all()
    this_campaign = Course.query.filter_by(id=id).first()
    courses = Course.query.filter_by(owner_id=current_user.id, status=1).all()
    code = this_campaign.url
    if this_campaign.color:
        color = this_campaign.color
    else:
        color = "#fffff"
    check_key = this_campaign.stripe_api_key
    return render_template('compaignusers.html',
                           active_compaign_id=int(id),
                           url = code,
                           users = users,
                           this_campaign = this_campaign,
                           compaign_id=compaign_id,
                           check_key =check_key,
                           courses=courses,
                           emailform = emailform,
                           customizeform = customizeform,
                           formu = form,keyform=keyform,
                           color = color,
                           delete_resource= delete_resource,
                           ResourcesForm= ResourcesForm,
                           compainform = compainform)

@courses.route('/courses/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        email = request.form['email']
        compaign = request.form['campaign']
        # You can now add the user to your database or perform any necessary operations.
        # Example:
        new_user = User(email=email, status=2, course_id = compaign)  # Assuming a User model
        db.session.add(new_user)
        db.session.commit()
        flash("User added successfully!", "success")
        return redirect(url_for('courses.dashboard', course = compaign))  # Redirect back to dashboard


@courses.route('/config/<id>', methods=['POST'])
@login_required
def config(id):
    form = OpenAiform()
    if form.validate_on_submit():
        key = form.key.data
        endpoint_secret = form.endpoint_secret.data
        product_id = form.product_id.data
        openai_key = form.openai_key.data
        compain = Course.query.filter_by(id = id).first()
        compain.stripe_api_key = key
        compain.product_id = product_id
        compain.endpoint_secret = endpoint_secret
        compain.openai_key = openai_key
        db.session.commit()  # Save the changes to t
        return redirect(url_for('courses.dashboard', course = id))

@courses.route('/delete_compain/<compaign>', methods=['POST'])
@login_required
def delete_compain(compaign):
    template_id = int(request.form.get('template_id'))  # Convert to integer
    email_template = EmailTemplate.query.filter_by(id=template_id).first()
    campaign = Course.query.filter_by(id = compaign).first()
    # delete campaign
    db.session.delete(email_template)
    db.session.commit()

    return redirect(url_for('courses.dashboard',course = campaign.id))
    
@courses.route('/delete_resource/<resource>', methods=['POST'])
@login_required
def delete_resource(resource):
    resource = CourseResource.query.filter_by(id=resource).first()
    campaign_id = resource.course
    # delete campaign
    db.session.delete(resource)
    db.session.commit()

    return redirect(url_for('courses.resources', campaign=campaign_id))

@courses.route('/delete_campaign/<campaign>', methods=['POST', 'GET'])
@login_required
def delete_campaign(campaign):
    # Fetch the campaign (course)
    resource = Course.query.filter_by(id=campaign).first()

    if not resource:
        flash('Campaign not found', 'error')
        return redirect(url_for('users.dashboard'))

    # Unsubscribe all users subscribed to this campaign (course)
    users_to_unsubscribe = User.query.filter_by(course_id=resource.id, status=2).all()

    success_count = 0
    failure_count = 0

    for user in users_to_unsubscribe:
        if unsubscribe_user(resource.stripe_api_key, user.payment_intent_id):
            success_count += 1
        else:
            failure_count += 1

    # Log or flash the result of the unsubscription process
    flash(f"Unsubscribed {success_count} users, {failure_count} failures.", 'info')

    # Deactivate the campaign (set status to 0)
    resource.status = 0
    db.session.commit()

    return redirect(url_for('users.dashboard'))
    
def unsubscribe_user(key, subscription_id):
    """
    Cancels a subscription using Stripe API.

    Args:
    - key (str): Stripe API key.
    - subscription_id (str): ID of the subscription to cancel.

    Returns:
    - bool: True if cancellation was successful, False otherwise.
    """
    try:
        stripe.api_key = key
        stripe.Subscription.delete(subscription_id)
        return True
    except stripe.error.StripeError as e:
        # Handle specific Stripe errors as needed
        print(f"Stripe error: {e}")
        return False
    except Exception as e:
        # Handle other exceptions
        print(f"Error: {e}")
        return False


@courses.route('/sendeditedemail/<compaign>', methods=['POST'])
@login_required
def sendeditedemail(compaign):
    users = User.query.filter_by(status=2, course_id=compaign).all()
    campaign = Course.query.filter_by(id=compaign).first()

    # Retrieve form data (header, body, footer, subject, and attachment)
    subject = campaign.name
    body = request.form['emailContent']
    template_header = ''
    footer = ''
    attachment = request.files.get('attachment')

    attachment_path = None
    attachment_filename = None

    # Handle file attachment if provided
    if attachment:
        attachment_filename = secure_filename(attachment.filename)
        attachment_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment_filename)

        # Ensure the upload folder exists
        if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
            os.makedirs(current_app.config['UPLOAD_FOLDER'])

        # Save the attachment file
        attachment.save(attachment_path)

    # Loop through users and send the email
    for user in users:
        send_emails(user.email, subject, template_header, body, footer, user.id, compaign, attachment_path, attachment_filename)

    # Flash a success message
    flash('Emails sent successfully!', 'success')

    # Redirect back to the campaign's dashboard or any relevant page
    return redirect(url_for('courses.dashboard', course=compaign))



@courses.route('/send_email/<compaign>', methods=['GET', 'POST'])
@login_required
def sendemail(compaign):
    users = User.query.filter_by(status=2, course_id=compaign).all()
    
    if request.method == 'POST':
        subject = request.form['subject']
        body = request.form['body']
        template_header = request.form['header']
        footer = request.form['footer']
        attachment = request.files.get('attachment')

        attachment_path = None
        attachment_filename = None
        if attachment:
            attachment_filename = secure_filename(attachment.filename)
            attachment_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment_filename)
            
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
            
            attachment.save(attachment_path)
        
        for user in users:
            send_emails(user.email, subject, template_header, body, footer, user.id, compaign, attachment_path, attachment_filename)
        
        flash('Emails sent successfully', 'success')
        return redirect(url_for('courses.dashboard', course=compaign))

    return render_template('send_email.html', campaign=campaign)
    
    
from sqlalchemy.exc import OperationalError
import logging
import sys

# Configure logging to handle Unicode characters
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
sys.stdout.reconfigure(encoding='utf-8')  # Ensure stdout supports UTF-8

from sqlalchemy import text

def keep_db_alive():
    try:
        # Correctly wrap the SQL query using SQLAlchemy's text() function
        db.session.execute(text('SELECT 1'))  
    except Exception as e:
        print(f"Error while keeping DB alive: {e}")
        db.session.rollback()  # Rollback any failed session to avoid leaving a bad session open


def generate_and_save_emails(template_id, campaign_id):
    with app.app_context():
        status_key = f"email_generation_status:{template_id}"
        redis_client.set(status_key, "in-progress")
        emails_to_save = []

        try:
            template = EmailTemplate.query.get(template_id)
            campaign = Course.query.filter_by(id=campaign_id).first()
            api_key = campaign.openai_key

            # Delete old emails
            GeneratedEmail.query.filter_by(template_id=template_id).delete()
            db.session.commit()
            logger.info(f"Deleted old emails for template {template_id}.")

            # Generate emails
            for _ in range(3):
                try:
                    keep_db_alive()
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                    conversation = conversation = [
    {
        "role": "system",
        "content": (
            "Eres un redactor profesional de newsletters. Tu tarea es generar un boletín informativo "
            "atractivo y profesional, dirigido a una audiencia real y específica."
        )
    },
    {
        "role": "user",
        "content": (
            f"Genera un boletín informativo completo basado en este tema: {template.header}. El contenido debe incluir:"
            f"\n- Un mensaje inicial atractivo que capte la atención del lector."
            f"\n- Un desarrollo claro y estructurado con detalles relevantes, como introducción, subtítulos naturales ('Nuestra Misión', 'Logros', etc.), y un llamado a la acción al final."
            f"\n- Un cierre profesional que invite a la interacción, todo en un formato fluido y natural."
            f"\nNo uses variables o marcadores de posición como '[Su nombre]', '[nombre de tu revista/empresa]', '[Email de Contacto]', etc."
            f"\nEl texto debe ser lo más detallado y profesional posible, pero siempre usando información ficticia realista si necesitas ejemplos."
            f"\nAñade emojis para captar atención y mantener el interés del lector."
            f"\nAsegúrate de que el texto esté limpio y que no contenga elementos genéricos que requieran reemplazo posterior."
        )
    }
]
 # Existing conversation logic
                    email_content = generate_response(conversation, headers, max_tokens=700)
                    formatted_body = convert_bold_to_html(email_content.replace('\n', '<br>\n').strip())
                    emails_to_save.append(GeneratedEmail(
                        header="",
                        body=formatted_body,
                        footer="",
                        template_id=template_id,
                        created_at=datetime.utcnow(),
                        conversation=json.dumps(conversation, ensure_ascii=False)
                    ))
                except Exception as e:
                    logger.error(f"Error generating email: {repr(e)}")

            # Bulk save emails
            if emails_to_save:
                db.session.bulk_save_objects(emails_to_save)
                db.session.commit()
                logger.info(f"Generated and saved emails for template {template_id}.")

            redis_client.set(status_key, "completed")
        except Exception as e:
            logger.error(f"Global error in email generation: {repr(e)}")
            redis_client.set(status_key, "failed")
        finally:
            redis_client.expire(status_key, 3600)

def convert_bold_to_html(content):
    """Converts markdown-style bold (**) to HTML <strong> tags."""
    while '**' in content:
        # Replace first occurrence of '**' with <strong>
        content = content.replace('**', '<b>', 1)
        # Replace next occurrence of '**' with </strong>
        content = content.replace('**', '</b>', 1)
    return content

def generate_response(conversation, headers, max_tokens, max_retries=3):
    """Sends a request to OpenAI's API and returns the response, with retry logic."""
    payload = {
        "model": "gpt-4",
        "messages": conversation,
        "max_tokens": max_tokens,
        "temperature": 1
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                content = response.json().get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                if content:
                    return content
                else:
                    print("Received empty content from API.")
                    return "<p>Error in content generation.</p>"

            elif response.status_code == 429:  # Rate limit
                print("Rate limit reached. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff

            else:
                print(f"Error in API response: {response.status_code} - {response.text}")
                return "<p>Error in content generation.</p>"

        except requests.exceptions.Timeout:
            print("Request timed out. Retrying...")

    print("Max retries exceeded.")
    return "<p>Failed to generate content after multiple attempts.</p>"


@courses.route('/sendgeneratedemail/<int:generated_email_id>/<int:compaign>', methods=['POST'])
@login_required
def send_generated_email(generated_email_id, compaign):
    # Retrieve the generated email by ID
    generated_email = GeneratedEmail.query.filter_by(id=generated_email_id).first()
    
    if not generated_email:
        flash('Generated email not found!', 'danger')
        return redirect(url_for('courses.dashboard', course=compaign))

    # Retrieve users associated with the campaign
    users = User.query.filter_by(status=2, course_id=compaign).all()

    # Retrieve the associated campaign
    campaign = Course.query.filter_by(id=compaign).first()

    if not campaign:
        flash('Campaign not found!', 'danger')
        return redirect(url_for('courses.dashboard', course=compaign))

    subject = campaign.name
    body = generated_email.body
    template_header = generated_email.header
    footer = generated_email.footer

    # Handle file attachment if provided (similar logic as your existing route)
    attachment = request.files.get('attachment')
    attachment_path = None
    attachment_filename = None

    if attachment:
        attachment_filename = secure_filename(attachment.filename)
        attachment_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment_filename)
        
        if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
            os.makedirs(current_app.config['UPLOAD_FOLDER'])
        
        attachment.save(attachment_path)

    # Loop through users and send the email
    for user in users:
        send_emails(
            user.email,
            subject,
            template_header,
            body,
            footer,
            user.id,
            compaign,
            attachment_path,
            attachment_filename
        )

    # Update the status of the generated email after sending
    generated_email.is_sent = True
    db.session.commit()

    # Flash a success message
    flash('Generated email sent successfully!', 'success')

    # Redirect back to the campaign's dashboard or any relevant page
    return redirect(url_for('courses.dashboard', course=compaign))
@courses.route('/regenerate_email/<int:generated_email_id>', methods=['POST'])
@login_required
def regenerate_email(generated_email_id):
    """
    Route to regenerate an email asynchronously using Redis.
    """
    # Redis key for tracking status
    redis_key = f"email_generation_status:{generated_email_id}"

    # Set initial status to in-progress
    redis_client.set(redis_key, "in-progress")

    # Trigger the regeneration task in a separate thread
    threading.Thread(target=regenerate_email_task, args=(generated_email_id, redis_key)).start()

    # Return success response immediately
    return jsonify({"message": "Regeneration initiated successfully."}), 200


def regenerate_email_task(generated_email_id, redis_key):
    """
    Regenerate an email's content using OpenAI, update the database, and use Redis for status tracking.
    """
    print("Background task running...")

    # Ensure that the Flask app context is available
    with app.app_context():
        try:
            # Fetch the GeneratedEmail object
            generated_email = GeneratedEmail.query.get(generated_email_id)
            if not generated_email:
                raise ValueError(f"No GeneratedEmail found with ID {generated_email_id}")

            # Load the conversation and update the prompt
            conversation_data = json.loads(generated_email.conversation)

            # Fetch campaign details
            campaign = Course.query.filter_by(id=generated_email.email_template.compaign).first()
            if not campaign or not campaign.openai_key:
                raise ValueError(f"No campaign or API key found for GeneratedEmail ID {generated_email_id}")

            # Update the user prompt to request a different version
            conversation_data[1]['content'] += (
                " Genera una versión completamente diferente de la que proporcionaste anteriormente. "
                "El boletín debe incluir un mensaje inicial atractivo, un desarrollo claro y bien estructurado, y un cierre profesional que invite a la interacción. "
                "Asegúrate de que sea un texto fluido, profesional y suficientemente detallado, sin etiquetas o separaciones explícitas como 'Encabezado', 'Cuerpo' o 'Pie de página'. "
                "No incluyas nombres personales ni información identificable de individuos."
            )

            # Generate new email content
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {campaign.openai_key}"
            }
            new_email_content = generate_response(conversation_data, headers, max_tokens=700)

            # Format the content
            formatted_body = new_email_content.replace('\n', '<br>\n').strip()  # Replace \n with <br>
            formatted_body = convert_bold_to_html(formatted_body)

            # Update the database with the new content
            generated_email.body = formatted_body
            generated_email.conversation = json.dumps(conversation_data, ensure_ascii=False)
            generated_email.is_sent = False  # Reset sent status
            generated_email.updated_at = datetime.utcnow()  # Optional: Track when the email was last updated

            db.session.commit()

            # Update Redis status to completed
            redis_client.set(redis_key, "completed")
            redis_client.expire(redis_key, 3600)  # Optional: Set an expiration for the key

            print(f"Email content regenerated successfully for GeneratedEmail ID {generated_email_id}")
        except OperationalError as e:
            db.session.rollback()
            error_message = f"Database operation failed: {repr(e)}"
            redis_client.set(redis_key, f"failed:Database error occurred: {repr(e)}")
            redis_client.expire(redis_key, 3600)  # Optional: Set an expiration for the key
            print(error_message)
        except Exception as e:
            error_message = f"An error occurred: {repr(e)}"
            redis_client.set(redis_key, f"failed:Unexpected error occurred: {repr(e)}")
            redis_client.expire(redis_key, 3600)  # Optional: Set an expiration for the key
            print(error_message)

@courses.route('/regenerate_all_emails/<int:template_id>', methods=['POST'])
@login_required
def regenerate_all_emails(template_id):
    """
    Handle regeneration of all emails asynchronously.
    """
    try:
        email_template = EmailTemplate.query.get_or_404(template_id)

        # Start regeneration in a separate thread
        threading.Thread(target=generate_and_save_emails, args=(template_id, email_template.compaign)).start()

        # Return JSON response with the template_id
        return jsonify({"message": "Regeneration initiated successfully.", "template_id": template_id}), 200
    except Exception as e:
        # Handle any errors
        return jsonify({"error": str(e)}), 500



@courses.route('/delete_email_template/<int:compaign>', methods=['POST'])
def delete_email_template(compaign):
    # Retrieve the email template by ID
    email_template = EmailTemplate.query.get_or_404(compaign)
    
    # Delete associated emails
    for email in email_template.generated_emails:
        db.session.delete(email)

    # Delete the template itself
    db.session.delete(email_template)
    db.session.commit()

    flash('Template and associated emails deleted successfully.', 'success')
    return redirect(url_for('courses.dashboard', course=email_template.compaign))

# dcqw whew eoyq gyki
@courses.route('/generate_email_body/<compaign>', methods=['POST'])
@login_required
def generate_email_body(compaign):
    # Retrieve template ID from request (assuming it's sent via POST)
    template_id = int(request.form.get('template_i'))  # Convert to integer
    campaign = Course.query.filter_by(id=compaign).first()
    
    # Provide your OpenAI API key here
    api_key = campaign.openai_key
    openai.api_key = api_key

    # Fetch email template from your database based on the template ID
    template = retrieve_email_template_from_database(template_id)

    # Generate header
    header_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""Genera el encabezado para una newsletter basándote en la siguiente indicación: {template.header}. No añadas ningún carácter adicional añade emojis relacionados con el tema."""}
    ]
    header_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=header_messages,
        max_tokens=500,
        temperature=1
    )
    header = header_completion.choices[0].message['content'].strip()

    # Generate body
    body_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""
                Genera el cuerpo para una newsletter con las siguientes instrucciones:

                El texto debe estar en español.
                Asegúrate de que los párrafos estén bien separados por 1 salto de línea.
                No escribas absolutamente nada que no tenga que ver con el articulo, por ejemplo no pongas asunto:texto del articulo encabezado:texto del encabezado... esto no lo tiene que ver el usuario.
                El articulo debe tener entre 3 y 5 parrafos separados con un salto de línea de unos 300 caracteres cada uno.
                No dejes información colgando, por ejemplo si no sabes nombre del autor o no sabes las redes sociales, no lo menciones.
                Devuelve el texto en formato html, con saltos de linea, las partes importantes en negrita o cursiva si fuese necesario.
                El tema sobre el que tienes que escribir es el siguiente : {template.body}
        """}
    ]
    body_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=body_messages,
        max_tokens=2000,
        temperature=1
    )
    body = body_completion.choices[0].message['content'].strip()

    # Generate footer
    footer_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""
            Genera el pie de página para una newsletter siguiendo las siguientes indicaciones:

            {template.footer}
            No añadas caracteres irrelevantes para el mensaje como guiones o cualquier otro carácter al inicio y el final del párrafo.
            No dejes información colgando, por ejemplo, si no sabes el nombre del autor o no sabes las redes sociales, no lo menciones.
            Recuerda despedirte con la siguiente información: ¡Gracias por ser parte de nuestra comunidad! Apreciamos tu interés. Esperamos que sigas disfrutando de nuestras curiosidades y artículos. Hasta la próxima entrega. ¡Gracias por estar con nosotros!
        """}
    ]
    footer_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=footer_messages,
        max_tokens=500,
        temperature=1
    )
    footer = footer_completion.choices[0].message['content'].strip()

    # Fetch users from the database whose status is 2
    users = User.query.filter_by(status=2, course_id=compaign).all()

    # Retrieve campaign-related variables similar to the /users route
    customizeform = Customizeform()
    form = Emailstemplate()
    keyform = OpenAiform()
    compainform = CourseForm()
    compaign_id = compaign  # Pass the compaign parameter
    emailform = Emailform()
    delete_resource = DeleteResource()
    ResourcesForm = CourseResourcesForm()

    this_campaign = Course.query.filter_by(id=compaign).first()
    courses = Course.query.filter_by(owner_id=current_user.id, status=1).all()

    # Handle campaign URL and color
    code = this_campaign.url if this_campaign else ""
    color = this_campaign.color if this_campaign and this_campaign.color else "#ffffff"
    check_key = this_campaign.stripe_api_key if this_campaign else None

    return render_template(
        'generatedemail.html',
        header=header,
        body=body,
        footer=footer,
        active_compaign_id=int(compaign),
        url=code,
        this_campaign=this_campaign,
        compaign_id=compaign_id,
        check_key=check_key,
        courses=courses,
        emailform=emailform,
        customizeform=customizeform,
        formu=form,
        keyform=keyform,
        color=color,
        delete_resource=delete_resource,
        ResourcesForm=ResourcesForm,
        compainform=compainform
    )

    
    # Send the generated email to each user
    # for user in users:
    # send_emails(recipient, subject, template_header, body, footer, user, campaign, attachment_path=None, attachment_filename=None)
    #     send_emails(user.email, header, template.header, body, footer, user.id, campaign.id)

    # # Flash a success message
    # flash("Emails sent successfully", "success")

    # # Redirect to the dashboard
    # return redirect(url_for('users.dashboard'))




