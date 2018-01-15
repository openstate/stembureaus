from flask import render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_required, login_user, logout_user, current_user
from app import app, db
from app.forms import RegisterForm, LoginForm
from app.models import User

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/over-deze-website")
def over_deze_website():
    return render_template('over-deze-website.html')

@app.route("/dataset")
def dataset():
    return render_template('dataset.html')

@app.route("/gemeente-aanmelden", methods=['GET', 'POST'])
def gemeente_aanmelden():
    if current_user.is_authenticated:
        return redirect(url_for('gemeente_stemlokalen_overzicht'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.Wachtwoord.data)
        db.session.add(user)
        db.session.commit()
        flash('Aanmelden gelukt')
        return redirect(url_for('gemeente_login'))
    return render_template('gemeente-aanmelden.html', form=form)

@app.route("/gemeente-login", methods=['GET', 'POST'])
def gemeente_login():
    if current_user.is_authenticated:
        return redirect(url_for('gemeente_stemlokalen_overzicht'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.Wachtwoord.data):
            flash('Fout e-mailadres of wachtwoord')
            return(redirect(url_for('gemeente_login')))
        login_user(user)
        return redirect(url_for('gemeente_stemlokalen_overzicht'))
    return render_template('gemeente-login.html', form=form)

@app.route("/gemeente-logout")
@login_required
def gemeente_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/gemeente-stemlokalen-overzicht", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_overzicht():
    return render_template('gemeente-stemlokalen-overzicht.html')

@app.route("/gemeente-stemlokalen-upload", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_upload():
    return render_template('gemeente-stemlokalen-upload.html')

if __name__ == "__main__":
    app.run(threaded=True)
