import requests
from django.conf import settings


class MailgunEmailService:
    def __init__(self):
        self.api_key = settings.MAILGUN_API_KEY
        self.domain = settings.MAILGUN_DOMAIN
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        self.from_email = settings.MAILGUN_FROM_EMAIL
        self.from_name = settings.MAILGUN_FROM_NAME

    def send_transactional_email(self, to_email, to_name, subject, html_content, text_content=None):
        """Send a single transactional email via Mailgun"""
        try:
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": f"{to_name} <{to_email}>",
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                data["text"] = text_content

            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                print(f"✅ Email sent successfully to {to_email}")
                return response.json()
            else:
                print(f"❌ Failed to send email to {to_email}")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Exception when sending email to {to_email}: {str(e)}")
            return None

    def send_bulk_email(self, recipients, subject, html_content, text_content=None):
        """Send bulk emails using Mailgun's batch sending"""
        try:
            # Mailgun supports up to 1000 recipients per API call
            to_list = [f"{r['name']} <{r['email']}>" for r in recipients]

            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_list,
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                data["text"] = text_content

            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                print(f"✅ Bulk email sent successfully to {len(recipients)} recipients")
                return response.json()
            else:
                print(f"❌ Failed to send bulk email")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Exception when sending bulk email: {str(e)}")
            return None
        

        