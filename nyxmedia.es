import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from auth.model import User
from course.model import Course
from emails.models import EmailTemplate
from server import app  # Replace with the actual import for your Flask app

import openai

def send_email(recipient, subject, template_header, body, footer, user, campaign):
    # Configure SMTP server settings
    smtp_server = 'mail.nyxmedia.es'
    smtp_port = 587
    sender_email = 'communication@nyxmedia.es'
    sender_password = 'Faustino69!'

    # Create a MIME multipart message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient
    message['Subject'] = template_header

    # Define the HTML content of the email
    image_url = 'https://nyxmedia-tonirodriguez.pythonanywhere.com/static/images/nyx_logo.jpeg'
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
                color: #fff;
                height: 60px;
                text-align: center;
                background-color: black;
                padding: 20px;
                border-radius: 10px;
            }}
            .footer-content{{
                margin-top: 10px;
            }}
            .footer-content1{{
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
            <img src="{image_url}" alt="Logo" height="100" width="100">
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
                <a href="https://nyxmedia.es/auth/unsubscribe/{user}/{campaign}" class="small-link">¿Deseas dejar de recibir nuestras actualizaciones? Haz clic aquí para cancelar tu suscripción.</a>
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

    # Attach the email body as HTML
    message.attach(MIMEText(html_content, 'html'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)


def main():
    with app.app_context():
        campaigns = Course.query.filter_by(type=1).all()
        for campaign in campaigns:
            api_key = campaign.openai_key
            if api_key is None:
                continue
            templates = EmailTemplate.query.filter_by(compaign=campaign.id).all()
            users = User.query.filter_by(status=2, course_id=campaign.id).all()
            openai.api_key = api_key
            for user in users:
                for template in templates:
                    # Generate header
                    header_messages = [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": f"Genera el encabezado para una newsletter basandote en la siguiente indicación: {template.header} , es muy importante que no haya ningún caracter que no aporte valor como guiones o comillas al principio ni al final del texto. Añade algún emoji que pueda cuadrar con el texto."}
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
                                Asegúrate de que los párrafos estén bien separados por saltos de línea.
                                No escribas absolutamente nada que no tenga que ver con el articulo, por ejemplo no pongas asunto:texto del articulo encabezado:texto del encabezado... esto no lo tiene que ver el usuario.
                                El articulo debe tener entre 3 y 5 parrafos separados con saltos de línea de unos 300 caracteres cada uno.
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
                            No añadas caracteres irrelevantes para el mensaje como guiones o cualquier otro caracter al inicio y el final del parrafo.
                            No dejes información colgando, por ejemplo si no sabes nombre del autor o no sabes las redes sociales, no lo menciones.
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

                    # send_email(user.email, header, template.header, body, footer, user.id, campaign.id)
                    send_email(user.email, header, template.header, body, footer, user.id, campaign.id)
                    
                    print("sent")


if __name__ == "__main__":
    main()
