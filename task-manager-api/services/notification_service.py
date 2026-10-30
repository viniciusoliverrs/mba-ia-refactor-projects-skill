import logging
import smtplib

from config.settings import Settings
from utils.helpers import utcnow

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.email_host = Settings.SMTP_HOST
        self.email_port = Settings.SMTP_PORT
        self.email_user = Settings.SMTP_USER
        self.email_password = Settings.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        if not self.email_user or not self.email_password:
            logger.info("SMTP não configurado; notificação registrada em log para %s", to)
            return False

        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except smtplib.SMTPException as exc:
            logger.error("Erro ao enviar email: %s", exc)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você at {utcnow()}.\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)
