from flask import render_template, request, redirect, url_for, flash
from flask_login import (
    UserMixin, login_required, login_user, logout_user, current_user
)
from app import app, db
from app.forms import ResetPasswordRequestForm, ResetPasswordForm, LoginForm
from app.email import send_password_reset_email
from app.models import User, ckan


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/over-deze-website")
def over_deze_website():
    return render_template('over-deze-website.html')


@app.route("/dataset")
def dataset():
    return render_template('dataset.html')


@app.route("/gemeente-reset-wachtwoord-verzoek", methods=['GET', 'POST'])
def gemeente_reset_wachtwoord_verzoek():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            'Er is een e-mail verzonden met instructies om het wachtwoord te '
            'veranderen'
        )
        return redirect(url_for('gemeente_login'))
    return render_template('gemeente-reset-wachtwoord-verzoek.html', form=form)


@app.route("/gemeente-reset-wachtwoord/<token>", methods=['GET', 'POST'])
def gemeente_reset_wachtwoord(token):
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.Wachtwoord.data)
        db.session.commit()
        flash('Uw wachtwoord is aangepast')
        return redirect(url_for('gemeente_login'))
    return render_template('gemeente-reset-wachtwoord.html', form=form)


@app.route("/gemeente-login", methods=['GET', 'POST'])
def gemeente_login():
    if current_user.is_authenticated:
        return redirect(url_for('gemeente_verkiezing_overzicht'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.Wachtwoord.data):
            flash('Fout e-mailadres of wachtwoord')
            return(redirect(url_for('gemeente_login')))
        login_user(user)
        return redirect(url_for('gemeente_verkiezing_overzicht'))
    return render_template('gemeente-login.html', form=form)


@app.route("/gemeente-logout")
@login_required
def gemeente_logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/gemeente-verkiezing-overzicht", methods=['GET', 'POST'])
@login_required
def gemeente_verkiezing_overzicht():
    return render_template(
        'gemeente-verkiezing-overzicht.html',
        elections=ckan.elections
    )


@app.route("/gemeente-stemlokalen-overzicht/<verkiezing>", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_overzicht(verkiezing):
    return render_template('gemeente-stemlokalen-overzicht.html', verkiezing=verkiezing)


@app.route("/gemeente-stemlokalen-edit", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_upload():
    return render_template('gemeente-stemlokalen-edit.html')

if __name__ == "__main__":
    app.run(threaded=True)
