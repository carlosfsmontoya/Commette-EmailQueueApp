import azure.functions as func
import logging
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = func.FunctionApp()

@app.queue_trigger(arg_name="azqueue", queue_name="email-queue",
                   connection="CommetteAzureWebJobsStorage")
def QueueTriggerFunctionActivateAccount(azqueue: func.QueueMessage):
    body = azqueue.get_body().decode('utf-8')

    logging.info("Procesando mensaje de la cola")
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))

    SECRET_KEY_FUNC = os.getenv('SECRET_KEY_FUNC')

    try:
        logging.info(f"Sending request to get activation code for {body}")
        response = requests.post(
            f"http://localhost:8000/user/{body}/code",
            headers={"Authorization": SECRET_KEY_FUNC}
        )
        response.raise_for_status()
        code = response.json().get('code')
        logging.info(f"Received activation code for {body}")

        message = MIMEText(f"Your activation code is: {code}")
        message['Subject'] = 'Test Email'
        message['From'] = sender
        message['To'] = body

        logging.info(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [body], message.as_string())
        logging.info(f"Email sent to {body}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error: {str(e)}")
    except Exception as e:
        logging.error(f"Failed to send email to {body}: {str(e)}")

    logging.info('Python Queue trigger processed a message: %s', body)