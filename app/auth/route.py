# auth.py
from flask import Blueprint, redirect,render_template,url_for,request, flash, abort,jsonify
from app.auth.forms import LoginForm, RegistrationForm, ContactForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template
from app.auth.model import User, db,Adminuser, AdminRole
from app.course.model import Course, CourseResource
import stripe
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid
from flask import session
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import requests
import json
import logging
from flask_login import current_user
from flask import request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask_login import login_user, logout_user, login_required
# This is your Stripe CLI webhook secret for testing your endpoint locally.


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(recipient, subject, body):
    # Configure SMTP server settings
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'nyxfundation@gmail.com'
    sender_password = 'tcrj fnli dzeu cyxg'

    # Create a MIME multipart message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient
    message['Subject'] = subject

    # Define the HTML content of the email
    image_url = 'https://nyxmedia.es/static/images/images/67,356x223+66+141/10911913/logo_nyx.png'
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                padding: 20px;
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
            .body {{
                font-size: 16px;
                line-height: 1.5;
            }}
            .footer {{
                font-size: 14px;
                color: #777;
                height: 60px;
                text-align: center;
                background-color: black;
            }}
            .footer-content{{
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
               nyxmedia/payments courses
            </div>
            <img src="{image_url}" alt="Logo" height="50" width="50">
            <br>
            <br>
            <div class="body">
            Es un placer saludarle, desde Nyx esperamos que disfrute de su compra, clique en el siguiente enlace para ver el contenido:
            <br>
            {body}
            <div class="footer">
                <p class="footer-content">&copy; 2024 nyxmedia/payments. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Attach the email body as HTML
    message.attach(MIMEText(html_content, 'html'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)


def create_customer(email, stripe_api_key):
    stripe.api_key = stripe_api_key
    customer = stripe.Customer.create(
        email=email
    )
    return customer.id


def create_and_update_recurring(product_id, unit_amount, key, course_id, currency):
    try:
        # Initialize the Stripe API with your secret key
        stripe.api_key = key

        # Create a new recurring price
        new_price = stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,  # Amount in cents
            currency=currency,
            recurring={"interval": "month"},  # Recurring interval
            metadata ={'course_id': course_id},
            tax_behavior= 'exclusive'  # Set tax behavior to exclusive
                
        )

        # Update the product's default price
        stripe.Product.modify(
            product_id,
            default_price=new_price.id
        )

        return new_price.id  # Return the ID of the created price
    except stripe.error.StripeError as e:
        print("Stripe Error:", e)
        return None

def create_default_price_and_update_product(product_id, unit_amount, key,course_id, currency):
    try:
        # Initialize the Stripe API with your secret key
        stripe.api_key = key

        # Create a new price
        new_price = stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,  # Amount in cents
            currency=currency,
           metadata ={'course_id': course_id}
        )

        # Update the product's default price
        stripe.Product.modify(
            product_id,
            default_price=new_price.id
        )

        return new_price.id  # Return the ID of the created price
    except stripe.error.StripeError as e:
        print("Stripe Error:", e)
        return None

def subscriptioncheckout(course_id, created_price_id, customer, success_url, stripe_api_key, quantity=1):
    stripe.api_key = stripe_api_key
    try:
        # Retrieve the original price to calculate IVA
        price_object = stripe.Price.retrieve(created_price_id)
        unit_amount = price_object['unit_amount']  # Amount in cents
        currency = price_object['currency']

        # Calculate the IVA (21%)
        iva_amount = int(round(unit_amount * 0.21))  # Calculate 21% IVA in cents

        # Create a new recurring price for IVA (21%) in Stripe
        iva_price = stripe.Price.create(
            unit_amount=iva_amount,
            currency=currency,
            recurring={"interval": "month"},  # Set to monthly recurrence
            product_data={
                "name": "IVA (21%)",
                "metadata": {"course_id": course_id}
            }
        )

        # Create a Checkout Session with both the product and IVA as line items
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            metadata={'course_id': course_id},
            customer=customer,
            line_items=[
                {
                    'price': created_price_id,
                    'quantity': quantity,
                },
                {
                    'price': iva_price.id,  # Use the dynamically created IVA price
                    'quantity': quantity,
                }
            ],
            subscription_data={
                'metadata': {
                    'course_id': course_id,
                }
            },
            customer_update={"address": "auto"},
            success_url=success_url,
            cancel_url=url_for('auth.cancel', _external=True),  # Replace with your actual cancel URL
        )

        # Print the entire session object for debugging
        print("Session object:", session)

        # Check if the subscription ID is available
        subscription_id = session.subscription
        if subscription_id:
            print("Subscription Id:", subscription_id)
        else:
            print("Subscription ID not found in session. Please check your configuration.")

        return session.url
    except stripe.error.StripeError as e:
        # Handle Stripe API errors
        print(f"Stripe error: {e.user_message}")
        return None
    except Exception as e:
        # Handle other possible errors
        print(f"Error: {e}")
        return None


def create_checkout_session(course_id, created_price_id, customer, success_url, stripe_api_key, quantity=1):
    stripe.api_key = stripe_api_key
    try:
        session = stripe.checkout.Session.create(
            payment_intent_data={'metadata': {'course_id': course_id}},
            success_url=success_url,
            mode='payment',
            metadata ={'course_id': course_id},
            payment_method_types=['card'],
            customer=customer,
            line_items=[{
                'price': created_price_id,
                'quantity': quantity,
            }],
            automatic_tax={"enabled": True},
            customer_update={"address": "auto"},
        )

        return session.url
    except Exception as e:
        print(f"Error creating Checkout Session: {e}")
        return None





def create_payment_intent(amount, currency, customer_id, course_id, stripe_api_key):
    stripe.api_key = stripe_api_key
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=customer_id,
            metadata={'course_id': course_id}
        )
        return intent
    except Exception as e:
        print(f"Error creating Payment Intent: {e}")
        return None



# Define a Flask Blueprint named 'auth_bp'
auth_bp = Blueprint('auth', __name__)



@auth_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')

        # Parse the event payload
        try:
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
            event_data = event['data']['object']
            
            # Get the customer_id from the event data to identify the User
            customer_id = event_data.get('customer')
            if not customer_id:
                raise ValueError("Customer ID not found in payload")

        except Exception as e:
            logging.error(f"Webhook parsing error: {e}")
            return jsonify({'error': 'Invalid payload format'}), 400

        # Find the User based on the customer_id
        user = User.query.filter_by(customer_id=customer_id).first()
        if not user:
            logging.error("User not found")
            return jsonify({'error': 'User not found'}), 404

        # Fetch the corresponding Course for the user
        course = Course.query.get(user.course_id)
        if not course:
            logging.error("Course not found for the user")
            return jsonify({'error': 'Course not found for the user'}), 404

        # Fetch the Super Admin (only one in the system)
        super_admin = Adminuser.query.filter_by(role=AdminRole.SUPER_ADMIN).first()
        if not super_admin or not super_admin.stripe_account_id:
            logging.error("Super Admin or Stripe account not found")
            return jsonify({'error': 'Super Admin or Stripe account not found'}), 400

        # Verify the webhook signature using the fetched endpoint_secret
        try:
            endpoint_secret = course.endpoint_secret
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logging.error(f"Webhook signature verification failed: {e}")
            return jsonify({'error': 'Invalid signature'}), 400

        # Handle the event based on its type
        if event['type'] == 'checkout.session.completed' or event['type'] == 'invoice.payment_succeeded':
            # Mark the user as registered and payment completed
            user.status = 2  # Status 2 means payment completed
            db.session.commit()

            # Calculate 10% of the total payment amount
            amount_for_super_admin = int(event_data['amount_total'] * 0.1)

            # Create a transfer to the Super Admin's Stripe account
            try:
                transfer = stripe.Transfer.create(
                    amount=amount_for_super_admin,
                    currency=event_data['currency'],
                    destination=super_admin.stripe_account_id,
                    transfer_group=f'user_{user.id}_payment_{event_data["id"]}'
                )
                logging.info(f"Transfer of {amount_for_super_admin} cents to Super Admin successful.")
            except Exception as e:
                logging.error(f"Transfer to Super Admin failed: {e}")
                return jsonify({'error': 'Transfer to Super Admin failed'}), 500

        # Handle the customer.subscription.created event
        elif event['type'] == 'customer.subscription.created':
            # Extract the subscription_id from the event
            subscription_id = event_data['id']

            # Update the User's payment_intent_id (acting as subscription ID)
            user.payment_intent_id = subscription_id
            db.session.commit()

            logging.info(f"User {user.id}'s subscription updated with subscription_id: {subscription_id}")

        return jsonify({'status': 'Webhook processed'}), 200

    except Exception as general_error:
        logging.error(f"Internal Server Error: {general_error}")
        return jsonify({'error': 'Internal Server Error'}), 500




def handle_checkout_session(session):
    # Implement your logic to handle the checkout session
    print(f"Checkout session completed: {session}")
    # For example, update user status, send email, etc.

def handle_subscription_updated(session):
    subscription_id = session['id']
    customer_id = session['customer']
    amount = 0

    if 'items' in session and 'data' in session['items']:
        for item in session['items']['data']:
            if 'price' in item and 'unit_amount' in item['price']:
                amount += item['price']['unit_amount']

    try:
        payment = User.query.filter_by(customer_id = customer_id).first()
        course = Course.query.filter_by(id=payment.course_id).first()
        if payment:
            payment.payment_intent_id = subscription_id
            payment.status = 2
            db.session.commit()
    except Exception as e:
        # Handle database update error
        print("Database update error:", e)


def handle_payment_intent_succeeded(payment_intent):
    # Extract necessary information from payment_intent
    payment_intent_id = payment_intent['id']
    customer = payment_intent['customer']
    amount = payment_intent['amount_received'] / 100  # Convert amount to dollars

    try:
        # Assuming you have a Payments model with appropriate fields
        payment = User.query.filter_by(customer_id=customer).first()
        course = Course.query.filter_by(id=payment.course_id).first()
        if payment:
            payment.payment_intent_id = payment_intent_id
            payment.status = 2  # Assuming '2' represents a successful payment status
            db.session.commit()
            if course.type != 1:
                send_email(payment.email, 'Course Subscription', course.courselink)
    except Exception as e:
        # Handle database update error
        print("Database update error:", e)

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

@auth_bp.route("/confirm")
def confirm():

    return render_template("unsubscribe.html")

@auth_bp.route("/unsubscribe/<user>/<campaign>", methods=['POST','GET'])
def unsubscribe(user,campaign):
    user_id = user
    if request.method == 'POST':
        user = User.query.filter_by(id=user_id, course_id = campaign).first()
        course = Course.query.filter_by(id=campaign).first()
        subscription_id = user.payment_intent_id
        key = course.stripe_api_key
        print(user, course, subscription_id, key)
        if unsubscribe_user(key, subscription_id):
            print("Unsubscribing")
            user.status = 1
            db.session.commit()
            return redirect(url_for('auth.confirm'))
        return "error in unsubscribing";
    return render_template('unsubscribe_confirm.html', user_id =user_id,campaign = campaign  )
def send_customer_email(recipient, subject, body):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'nyxfundation@gmail.com'
    sender_password = 'tcrj fnli dzeu cyxg'  # Consider using environment variables for credentials

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient
    message['Subject'] = subject

    image_url = 'https://prueba.nyxmedia.es/images/67%2C356x223%2B66%2B141/10911913/logo_nyx.png'
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                padding: 20px;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .logo {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .body {{
                font-size: 16px;
                line-height: 1.6;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background-color: black;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="logo">
                <img src="{image_url}" alt="NYX Logo" style="height: auto; max-width: 150px;">
            </div>
            <div class="body">
                {body}
            </div>
            <div class="footer">
                <p>© 2024 NYX Media. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
            return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

@auth_bp.route('/', methods=['GET', 'POST'])
def landing():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            name = form.name.data
            phone = form.phone.data
            email = form.email.data
            message = form.message.data
            
            recipient = 'info@nyxmedia.es'
            subject = 'Nueva consulta de cliente - NYX Media'
            body = f"""
                <h2>Detalles del contacto:</h2>
                <p><strong>Nombre:</strong> {name}</p>
                <p><strong>Teléfono:</strong> {phone}</p>
                <p><strong>Email:</strong> {email}</p>
                <h3>Mensaje:</h3>
                <p>{message}</p>
            """
            
            if send_customer_email(recipient, subject, body):
                flash('¡Mensaje enviado correctamente!', 'success')
            else:
                flash('Error al enviar el mensaje. Por favor, inténtelo de nuevo.', 'error')
                
            return redirect(url_for('auth_bp.landing'))
            
        except Exception as e:
            flash('Error al enviar el mensaje. Por favor, inténtelo de nuevo.', 'error')
            print(f"Error en el formulario: {str(e)}")
            
    return render_template('landing/index.html', form=form)

@auth_bp.route("/termsandconditions")
def termsandconditions():
    return render_template('terms_and_condition.html')

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect authenticated users to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('users.dashboard'))  
    form = LoginForm()
    if form.validate_on_submit():
        # Retrieve the user based on the provided email
        user = Adminuser.query.filter_by(email=form.email.data).first()
        if user:
            # Check if the password is correct
            if user.check_password(form.password.data):  # Use the check_password method
                if user.is_verified:
                    login_user(user, remember=form.remember.data)
                    # Redirect based on user role or type
                    return redirect(url_for('users.dashboard'))  # Replace 'users.dashboard' with the appropriate endpoint
                else:
                    flash('Please verify your email before logging in.', 'warning')
            else:
                flash('Incorrect password. Please try again.', 'danger')
        else:
            flash('User does not exist. Please try again.', 'danger')

    # Render the login template with the login form
    return render_template('login.html', form=form)


@auth_bp.route('/success')
def success():
    return render_template('success.html')

@auth_bp.route('/cancel')
def cancel():
    return render_template('cancel.html')
@auth_bp.route('/logout')
def logout():
    # Log out the user
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register/<code>', methods=['GET', 'POST'])
def register(code):
    course = Course.query.filter_by(url=code).first()
    if not course:
        return redirect(url_for('auth.error', type=2))

    resources = CourseResource.query.filter_by(course=course.id).all()
    colo = course.color
    title = course.title
    price = course.price
    product = course.product_id
    key = course.stripe_api_key
    amount = int(round(price * 100))  # Ensure amount is an integer
    currency = course.currency if course.currency else "usd"

    if request.method == 'POST':
        # Manually retrieve form data
        email = request.form.get("form_393242570[ed-f-393242573]")  # Email input name
        

        # Basic validation check (you can add more if needed)
        if not email:
            print("Form validation failed. Missing required fields.")
            return redirect(url_for('auth.error', type=1))

        # Check if the email is already registered in this campaign
        existing_user = User.query.filter_by(email=email, course_id=course.id, status=2).first()
        if existing_user:
            return redirect(url_for('auth.error', type=1))
        
        

        try:
            if course.free:  # If the course is free
                print("Course is free, setting user status to 2.")
                # Add the new user with status 2 (already enrolled/registered)
                new_user = User(
                    email=email,
                    status=2,
                    course_id=course.id
                )
                db.session.add(new_user)
                db.session.commit()
                print("New user added to the database with status 2 (free course).")
                return redirect(url_for('auth.success'))  # Redirect to success page

            else:  # If the course is not free, proceed with Stripe payment
                print("Creating Stripe customer...")
                created_customer = create_customer(email, key)

                if course.type == 1:
                    created_price_id = create_and_update_recurring(product, amount, key, course.id, currency)
                else:
                    created_price_id = create_default_price_and_update_product(product, amount, key, course.id, currency)

                # Define success URL
                success_url = url_for('auth.success', _external=True)

                # Create a Checkout Session
                print("Creating Checkout Session...")
                if course.type == 1:
                    checkout_session_url = subscriptioncheckout(course.id, created_price_id, created_customer, success_url, key, quantity=1)
                else:
                    checkout_session_url = create_checkout_session(course.id, created_price_id, created_customer, success_url, key, quantity=1)

                if not checkout_session_url:
                    print("Failed to create Checkout Session")
                    return redirect(url_for('auth.error', type=3))

                print(f"Created Checkout Session URL: {checkout_session_url}")

                # Add the new user to the database session
                print("Adding new user to the database...")
                new_user = User(
                    email=email,
                    customer_id=created_customer,
                    amount=amount,
                    status=1,  # Status 1 = Payment Pending
                    course_id=course.id
                )
                db.session.add(new_user)
                db.session.commit()
                print("New user added to the database with status 1 (payment pending).")

                # Redirect to the checkout session URL after successful registration
                return redirect(checkout_session_url)

        except Exception as e:
            print(f"Error during registration process: {e}")
            return redirect(url_for('auth.error', type=3))

    # Render the registration form template
    return render_template('landing/subpage/index.html', color=colo, title=title, code=code, resources=resources)

@auth_bp.route('/verify/<token>')
def verify_email(token):
    user = Adminuser.verify_verification_token(token)
    if not user:
        flash('The verification link is invalid or has expired.')
        return redirect(url_for('auth.login'))
    # Mark user as verified
    user.is_verified = True  # You'll need to add this field to the Adminuser model
    db.session.commit()
    flash('Your email has been verified. You can now log in.')
    return redirect(url_for('auth.login'))





@auth_bp.route('/admin_register', methods=['GET', 'POST'])
def register_admin():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password before storing it in the database
        hashed_password=generate_password_hash(form.password.data, method='pbkdf2:sha256')
        
        # Create a new admin user with the hashed password
        new_admin = Adminuser(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password  # Store the hashed password
        )
        db.session.add(new_admin)
        db.session.commit()
        
        # Generate a verification token
        token = new_admin.generate_verification_token()
        
        # Generate verification URL
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        
        # Email body
        body = f'Thank you for registering! Please verify your account by clicking on the link: {verify_url}'
        
        # Send verification email
        send_email(new_admin.email, "Email Verification", body)
        
        # Flash success message
        flash('Admin user created successfully! Please verify your email before logging in.', 'success')
        
        # Redirect to login page
        return redirect(url_for('auth.login'))
    
    # Render the registration template with the form
    return render_template('admin_register.html', form=form)


@auth_bp.route('/error/<type>')
def error(type):
    message = ""
    if type == '1':
        message  =  "Sorry , You are not allowed to register in the same compaign twice";
    if type == '2':
        message = "Sorry, the compaign does not exist"
    return render_template('404.html', message = message)

@auth_bp.route('/email')
def temp():
    return render_template("email_template.html")