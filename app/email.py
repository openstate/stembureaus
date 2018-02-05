from flask import render_template
from flask_mail import Message
from app import app, mail


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        '[waarismijnstemlokaal.nl] Wachtwoord aanpassen',
        sender=app.config['FROM'],
        recipients=[user.email],
        text_body=render_template(
            'email/reset_password.txt',
            user=user,
            token=token
        ),
        html_body=render_template(
            'email/reset_password.html',
            user=user,
            token=token
        )
    )


# Sends an invite to all participating gemeenten (to be only used once!)
def send_invite(user):
    token = user.get_reset_password_token()
    send_email(
        'Uitnodiging deelname waarismijnstemlokaal.nl',
        sender=app.config['FROM'],
        recipients=[user.email],
        text_body=render_template(
            'email/uitnodiging.txt',
            user=user,
            token=token
        ),
        html_body=render_template(
            'email/uitnodiging.html',
            user=user,
            token=token
        )
    )
