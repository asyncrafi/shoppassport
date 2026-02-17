import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class MailgunEmailService:
    def __init__(self):
        self.api_key = settings.MAILGUN_API_KEY
        self.domain = settings.MAILGUN_DOMAIN
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        self.from_email = settings.MAILGUN_FROM_EMAIL
        self.from_name = settings.MAILGUN_FROM_NAME
        logger.info(f"📧 Mailgun Service initialized for domain: {self.domain}")

    def send_transactional_email(self, to_email, to_name, subject, html_content, text_content=None, attachment=None):
        """Send a single transactional email via Mailgun with optional attachments - ALWAYS sends email"""
        try:
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": f"{to_name} <{to_email}>",
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                data["text"] = text_content

            # Handle file attachments (optional - email still sent even without attachment)
            files = None
            attachment_status = "(no attachment)"
            
            if attachment:
                files = {}
                if isinstance(attachment, str):
                    # If it's a file path string
                    try:
                        with open(attachment, 'rb') as f:
                            file_content = f.read()
                            files['attachment'] = (attachment.split('/')[-1], file_content)
                        logger.info(f"✅ Attachment loaded: {attachment}")
                        attachment_status = f"(PDF attached: {attachment.split('/')[-1]})"
                    except FileNotFoundError:
                        logger.error(f"❌ File not found: {attachment} - Sending WITHOUT attachment")
                        attachment_status = "(attachment not found - sending without)"
                        files = None
                    except Exception as e:
                        logger.error(f"❌ Error loading attachment {attachment}: {str(e)}")
                        attachment_status = f"(attachment error - sending without)"
                        files = None
                        
                elif isinstance(attachment, dict):
                    # If it's a dict with file_path and other metadata
                    file_path = attachment.get('file_path')
                    if file_path:
                        try:
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                                files['attachment'] = (attachment.get('file_name', file_path.split('/')[-1]), file_content)
                            logger.info(f"✅ Attachment loaded: {file_path}")
                            attachment_status = "(PDF attached)"
                        except FileNotFoundError:
                            logger.error(f"❌ File not found: {file_path} - Sending WITHOUT attachment")
                            attachment_status = "(attachment not found - sending without)"
                            files = None
                        except Exception as e:
                            logger.error(f"❌ Error loading attachment {file_path}: {str(e)}")
                            attachment_status = "(attachment error - sending without)"
                            files = None

            logger.info(f"📤 Sending email to {to_email} {attachment_status}")
            
            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data=data,
                files=files,
                timeout=10
            )

            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"✅ Email SENT to {to_email}")
                logger.info(f"📬 Mailgun ID: {response_data.get('id', 'N/A')}")
                print(f"✅ Email sent successfully to {to_email}")
                print(f"📨 Mailgun Response: {response_data}")
                return response_data
            else:
                logger.error(f"❌ Email FAILED for {to_email}")
                logger.error(f"❌ Status: {response.status_code} | Response: {response.text}")
                print(f"❌ Failed to send email to {to_email}")
                print(f"❌ Status Code: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request Exception for {to_email}: {str(e)}")
            print(f"❌ Exception when sending email: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected Exception for {to_email}: {str(e)}")
            print(f"❌ Unexpected error: {str(e)}")
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
        

        