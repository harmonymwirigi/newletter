from app import db, redis
from app.course.model import Course
from app.emails.models import EmailTemplate, GeneratedEmail
from datetime import datetime
import requests
import json
from sqlalchemy.exc import OperationalError
from rq import Queue
import time

# Connect to the RQ Queue
task_queue = Queue(connection=redis)

def regenerate_email_task(generated_email_id):
    """
    Regenerate an email's content using OpenAI and update the database.
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
            new_email_content = generate_response(conversation_data, headers, max_tokens=2500)

            # Log AI response (optional, for debugging)
            print("AI Response for Regenerated Email:", new_email_content)

            # Update the database with the new content
            generated_email.body = new_email_content.strip()
            generated_email.conversation = json.dumps(conversation_data, ensure_ascii=False)
            generated_email.is_sent = False  # Reset sent status
            generated_email.updated_at = datetime.utcnow()  # Optional: Track when the email was last updated

            db.session.commit()
            return f"Email content regenerated successfully for GeneratedEmail ID {generated_email_id}"

        except OperationalError as e:
            db.session.rollback()
            print(f"Database operation failed: {repr(e)}")
            return f"Failed to regenerate email content for GeneratedEmail ID {generated_email_id}: {repr(e)}"
        except Exception as e:
            print(f"An error occurred: {repr(e)}")
            return f"An error occurred while regenerating email for GeneratedEmail ID {generated_email_id}: {repr(e)}"


def generate_and_save_emails_task(template_id, campaign_id):
    """
    Generate and save email variations using OpenAI's API for a specific template and campaign.
    """
    # Ensure that the Flask app context is available
    with app.app_context():
        try:
            # Fetch template and campaign from the database
            template = EmailTemplate.query.get(template_id)
            campaign = Course.query.filter_by(id=campaign_id).first()

            if not template or not campaign:
                print(f"Invalid template_id {template_id} or campaign_id {campaign_id}.")
                return

            api_key = campaign.openai_key
            if not api_key:
                print(f"No OpenAI API key found for campaign {campaign_id}.")
                return

            # Generate 3 variations of email content
            generated_emails = generate_email_variations(template, api_key, 3)
            if generated_emails:
                # Save all generated emails to the database
                save_generated_emails_to_db(generated_emails, template_id)

        except Exception as e:
            print(f"An error occurred in generating and saving emails: {repr(e)}")


def generate_email_variations(template, api_key, num_variations=3):
    """
    Generate a list of email variations using OpenAI API.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    conversation = [
        {
            "role": "system",
            "content": (
                "Eres un redactor profesional de newsletters. Tu tarea es generar un boletín informativo "
                "atractivo y profesional."
            )
        },
        {
            "role": "user",
            "content": (
                f"Genera un boletín informativo completo basado en este tema: {template.header}. El contenido debe incluir:"
                f"\n- Un mensaje inicial atractivo que capte la atención del lector."
                f"\n- Un desarrollo claro y estructurado con detalles relevantes, como introducción, subtítulos naturales ('Nuestra Misión', 'Logros', etc.), y un llamado a la acción al final."
                f"\n- Un cierre profesional que invite a la interacción, todo en un formato fluido y natural, sin etiquetas o separaciones explícitas como 'Encabezado', 'Cuerpo' o 'Pie de página'."
                f"\nAsegúrate de que el boletín sea profesional, atractivo y suficientemente detallado para el lector."
            )
        }
    ]

    email_variations = []

    for _ in range(num_variations):
        try:
            email_content = generate_response(conversation, headers, max_tokens=2500)
            email_variations.append(email_content.strip())
        except Exception as e:
            print(f"An error occurred while generating an email variation: {repr(e)}")

    return email_variations


def save_generated_emails_to_db(generated_emails, template_id):
    """
    Save generated email variations to the database.
    """
    try:
        for email_content in generated_emails:
            generated_email = GeneratedEmail(
                header="",  # No separate header for the full content
                body=email_content,
                footer="",  # No separate footer
                template_id=template_id,
                created_at=datetime.utcnow(),
                conversation=json.dumps([], ensure_ascii=False)  # No conversation for this
            )
            db.session.add(generated_email)

        db.session.commit()
    except OperationalError as e:
        db.session.rollback()
        print(f"Database operation failed: {repr(e)}")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred while saving the emails to the database: {repr(e)}")


def generate_response(conversation, headers, max_tokens, max_retries=3):
    """
    Sends a request to OpenAI's API and returns the response, with retry logic.
    """
    payload = {
        "model": "gpt-4",
        "messages": conversation,
        "max_tokens": max_tokens,
        "temperature": 0.7
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
        except Exception as e:
            print(f"An unexpected error occurred: {repr(e)}")

    print("Max retries exceeded.")
    return "<p>Failed to generate content after multiple attempts.</p>"
