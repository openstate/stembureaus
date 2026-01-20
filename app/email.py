from flask import render_template, current_app
from flask_mail import Message
from flask_mail import Mail

mail = Mail()

def send_email(subject, sender, recipients, text_body, html_body, debug = False):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if debug:
        return msg
    else:
        mail.send(msg)

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    with current_app.app_context():
        send_email(
            '[WaarIsMijnStemlokaal.nl] Wachtwoord veranderen',
            sender=current_app.config['FROM'],
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
    with current_app.app_context():
        send_email(
            'Uitnodiging deelname WaarIsMijnStemlokaal.nl',
            sender=current_app.config['FROM'],
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


# Sends an update email to all users
def send_update(user):
    with current_app.app_context():
        send_email(
            "Publiceer uw stemlokalen weer op WaarIsMijnStemlokaal.nl",
            sender=current_app.config['FROM'],
            recipients=[user.email],
            text_body=render_template(
                'email/update.txt',
                user=user
            ),
            html_body=render_template(
                'email/update.html',
                user=user
            )
        )


# Sends an email about changed stembureau data
def send_changed_data(gemeente, user, time_phrase, changes, debug = False):
    with current_app.app_context():
        return send_email(
            "Overzicht van gewijzigde gegevens op WaarIsMijnStemlokaal.nl",
            sender=current_app.config['FROM'],
            recipients=[user.email],
            text_body=render_template(
                'email/changed_data.txt',
                gemeente=gemeente,
                user=user,
                time_phrase=time_phrase,
                changes=changes
            ),
            html_body=render_template(
                'email/changed_data.html',
                gemeente=gemeente,
                user=user,
                time_phrase=time_phrase,
                changes=changes
            ),
            debug=debug
        )

# Sends an email that the number of municipalities that have published data has decreased
def send_published_decreased(gemeenten):
    with current_app.app_context():
        return send_email(
            "ALERT: gepubliceerde gemeenten verdwenen van WaarIsMijnStemlokaal.nl",
            sender=current_app.config['FROM'],
            recipients=current_app.config['ADMINS'],
            text_body=render_template(
                'email/published_decreased.txt',
                gemeenten=gemeenten
            ),
            html_body=render_template(
                'email/published_decreased.html',
                gemeenten=gemeenten
            )
        )
