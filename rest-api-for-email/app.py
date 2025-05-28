import sys
from flask import Flask, make_response, request, jsonify
import re
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from http import HTTPStatus

app = Flask(__name__)
load_dotenv()  # Load environment variables from .env file

# Load sender credentials from environment
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
if not (SENDER_EMAIL or APP_PASSWORD):
    print(
        f"Missing environment variables {"SENDER_EMAIL" if not SENDER_EMAIL else ""} {"APP_PASSWORD" if not APP_PASSWORD else ""}"
    )
    sys.exit(1)


# --- Validation Functions ---
def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def validate_subject(subject):
    return isinstance(subject, str) and 1 <= len(subject) <= 100


def validate_body(body):
    return isinstance(body, str) and len(body.strip()) > 0


# --- API Route ---
@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify({"status": "error", "message": "no parsable json body found"}),
            HTTPStatus.BAD_REQUEST,
        )

    email = data.get("email")
    subject = data.get("subject")
    body = data.get("body")

    errors = {}

    if not validate_email(email):
        errors["email"] = "Invalid email format."
    if not validate_subject(subject):
        errors["subject"] = "Subject must be between 1 and 100 characters."
    if not validate_body(body):
        errors["body"] = "Body must not be empty."

    if errors:
        return jsonify({"status": "error", "errors": errors}), HTTPStatus.BAD_REQUEST

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = email
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

        return (
            jsonify({"status": "success", "message": "Email sent successfully!"}),
            HTTPStatus.OK,
        )  # Success

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Failed to send email: {str(e)}"}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


# --- Error handling for unknown routes ---
@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error="Not found!"), 404)


# --- Entry Point ---
if __name__ == "__main__":
    app.run(debug=True)
