import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_test_email():
    smtp_server = 'mail.nyxmedia.es'
    smtp_port = 587
    sender_email = 'info@nyxmedia.es'
    sender_password = 'Faustino69!'
    recipient_email = 'harmonymwithalii@gmail.com'

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = 'Test Email'

    body = 'This is a test email.'
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
            print(f"Test email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send test email to {recipient_email}: {e}")

send_test_email()
