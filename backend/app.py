from flask import Flask, request
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
import os
import requests
from flask import redirect, session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText

load_dotenv()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

GMAIL_REDIRECT_URI = "http://127.0.0.1:5000/oauth2callback"
@app.route("/authorize-gmail")
@app.route("/authorize-gmail")
def authorize_gmail():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GMAIL_REDIRECT_URI]
            }
        },
        scopes=GMAIL_SCOPES,
        autogenerate_code_verifier=False
    )

    flow.redirect_uri = GMAIL_REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="false",
        prompt="consent"
    )

    session["gmail_state"] = state

    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GMAIL_REDIRECT_URI]
            }
        },
        scopes=GMAIL_SCOPES,
        state=session.get("gmail_state"),
        autogenerate_code_verifier=False
    )

    flow.redirect_uri = GMAIL_REDIRECT_URI

    flow.fetch_token(authorization_response=request.url)

    with open("gmail_token.json", "w") as token:
        token.write(flow.credentials.to_json())

    return "Gmail authorization successful! You can close this page."
def send_email(to_email, subject, body):
    try:
        creds = Credentials.from_authorized_user_file(
            "gmail_token.json",
            GMAIL_SCOPES
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject

        raw_message = {
            "raw": __import__("base64").urlsafe_b64encode(
                message.as_bytes()
            ).decode()
        }

        service.users().messages().send(
            userId="me",
            body=raw_message
        ).execute()

        return True

    except Exception as e:
        print("EMAIL ERROR:", e)
        return False

@app.route("/")
def home():
    return {"message": "Hairdrama Task Management Backend is running"}


@app.route("/api/test-db")
def test_db():
    try:
        response = supabase.table("tasks").select("*").limit(5).execute()

        return {
            "success": True,
            "tasks": response.data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500

@app.route("/api/tasks", methods=["POST"])
def create_task():
    try:
        data = request.json

        title = data.get("title")
        description = data.get("description")
        created_by = data.get("created_by")
        assigned_to = data.get("assigned_to")
        due_date = data.get("due_date")
        due_time = data.get("due_time")

        

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {
                "success": False,
                "error": "Authorization token is missing"
            }, 401

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/tasks",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": auth_header,
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json={
                "title": title,
                "description": description,
                "created_by": created_by,
                "assigned_to": assigned_to,
                "due_date": due_date,
                "due_time": due_time
            }
        )

        if response.status_code >= 400:
            return {
                "success": False,
                "error": response.text
            }, response.status_code

        task = response.json()[0]

        email_sent = False

        if assigned_to:
            user_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/profiles",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                params={
                    "select": "email,name",
                    "id": f"eq.{assigned_to}"
                }
            )

            if user_response.status_code < 400:
                users = user_response.json()

                if users:
                    assigned_user = users[0]

                    assigned_email = assigned_user.get("email")
                    assigned_name = assigned_user.get("name") or "User"

                    if assigned_email:
                        email_sent = send_email(
                            assigned_email,
                            f"New Task Assigned: {title}",
                            f"""Hello {assigned_name},

A new task has been assigned to you.

Task: {title}

Description: {description or "No description"}

Due Date: {due_date or "Not specified"}
Due Time: {due_time or "Not specified"}

Please check the task management application for more details.

Thank you,
Hairdrama Task Management"""
                        )

        return {
            "success": True,
            "task": task,
            "email_sent": email_sent
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500
    
@app.route("/api/tasks/<task_id>/complete", methods=["PUT"])
def complete_task(task_id):
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {
                "success": False,
                "error": "Authorization token is missing"
            }, 401

        # Get task details
        task_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/tasks",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": auth_header,
                "Content-Type": "application/json"
            },
            params={
                "select": "*",
                "id": f"eq.{task_id}"
            }
        )

        if task_response.status_code >= 400:
            return {
                "success": False,
                "error": task_response.text
            }, task_response.status_code

        tasks = task_response.json()

        if not tasks:
            return {
                "success": False,
                "error": "Task not found"
            }, 404

        task = tasks[0]

        # Mark task as completed
        update_response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/tasks",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": auth_header,
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            params={
                "id": f"eq.{task_id}"
            },
            json={
                "status": "completed"
            }
        )

        if update_response.status_code >= 400:
            return {
                "success": False,
                "error": update_response.text
            }, update_response.status_code

        # Send completion email
        email_sent = False

        assigned_to = task.get("assigned_to")

        if assigned_to:
            user_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/profiles",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                params={
                    "select": "email,name",
                    "id": f"eq.{assigned_to}"
                }
            )

            if user_response.status_code < 400:
                users = user_response.json()

                if users:
                    assigned_user = users[0]

                    assigned_email = assigned_user.get("email")
                    assigned_name = assigned_user.get("name") or "User"

                    if assigned_email:
                        email_sent = send_email(
                            assigned_email,
                            f"Task Completed: {task.get('title')}",
                            f"""Hello {assigned_name},

The following task has been completed:

Task: {task.get('title')}

Description: {task.get('description') or 'No description'}

The task has been marked as completed in the Hairdrama Task Management application.

Thank you,
Hairdrama Task Management"""
                        )

        return {
            "success": True,
            "task": update_response.json()[0],
            "email_sent": email_sent
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


@app.route("/api/users", methods=["GET"])
def get_users():
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {
                "success": False,
                "error": "Authorization token is missing"
            }, 401

        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": auth_header,
                "Content-Type": "application/json"
            },
            params={
                "select": "*"
            }
        )

        if response.status_code >= 400:
            return {
                "success": False,
                "error": response.text
            }, response.status_code

        return {
            "success": True,
            "users": response.json()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500
    

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {
                "success": False,
                "error": "Authorization token is missing"
            }, 401

        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/tasks",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": auth_header,
                "Content-Type": "application/json"
            },
            params={
                "select": "*",
                "order": "created_at.desc"
            }
        )

        if response.status_code >= 400:
            return {
                "success": False,
                "error": response.text
            }, response.status_code

        return {
            "success": True,
            "tasks": response.json()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))