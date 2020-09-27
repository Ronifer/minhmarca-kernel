import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDER = 'noreply@minhamarca.app'
SENDERNAME = 'Equipe Minha Marca'
USERNAME_SMTP = "AKIATHXEKS25KSEYYM5C"
PASSWORD_SMTP = "BJfoKgYvrIccZd7bwZ8UuoSWHwLxAbycjVIuscb+lkBe"
HOST = "email-smtp.us-east-1.amazonaws.com"
PORT = 587
SUBJECT = 'Teste de envio de email em massa'
BODY_HTML = open("minhamarca_mail_template.html").read()


def send_mail(recipient):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = SUBJECT
    msg['From'] = email.utils.formataddr((SENDERNAME, SENDER))
    msg['To'] = recipient
    body = MIMEText(BODY_HTML, 'html')

    msg.attach(body)

    server = smtplib.SMTP(HOST, PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(USERNAME_SMTP, PASSWORD_SMTP)
    server.sendmail(SENDER, recipient, msg.as_string())
    server.close()


leads = ['ronifersilva@icloud.com',
         'hay.carolina@hotmail.com', 'rsilva@vanzolini-ead.org.br']

for lead in leads:
    send_mail(lead)
