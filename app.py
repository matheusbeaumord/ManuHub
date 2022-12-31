# # required packages.
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'


db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(UserMixin, db.Model):
    db.init_app(app)

    login = LoginManager(app)
    login.login_view = 'login'
    login.init_app(app)
    # primary keys are required by SQLAlchemy
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User{self.username}"

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))


class Menu(db.Model):
    # primary keys are required by SQLAlchemy
    id = db.Column(db.Integer, primary_key=True, unique=True)
    nome = db.Column(db.String(64), index=True)
    categoria = db.Column(db.String(120))
    valor = db.Column(db.Integer())

    def __init__(self, nome, categoria, valor):
        self.nome = nome
        self.categoria = categoria
        self.valor = valor


with app.app_context():
    if __name__ == '__main__':
        db.create_all()
        app.run(debug=True)

# applications routes.


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_post():
    # login code goes here
    email = request.form.get('email')
    password_hash = request.form.get('password_hash')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password_hash, password_hash):
        flash('Please check your login details and try again.')
        # if the user doesn't exist or password is wrong, reload the page
        return redirect(url_for('login'))

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('menu'))


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup_post():
    # code to validate and add user to database goes here
    email = request.form.get('email')
    username = request.form.get('username')
    password_hash = request.form.get('password_hash')

    # if this returns a user, then the email already exists in database
    user = User.query.filter_by(email=email).first()

    if user:  # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, username=username,
                    password_hash=generate_password_hash(password_hash, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    flash('Success')
    return redirect(url_for('login'))


@app.route('/menu')
@login_required
def menu():
    pratos = Menu.query.all()
    return render_template('menu.html', pratos=pratos)


@app.route('/menu', methods=['POST'])
def menu_post():
    nome = request.form.get('nome')
    categoria = request.form.get('categoria')
    valor = request.form.get('valor')

    prato = Menu.query.filter_by(nome=nome).first()

    if prato:
        print('entrou no if')
        flash('Um prato com esse nome ja foi cadastrado')
        return redirect(url_for('menu'))

    new_prato = Menu(nome=nome, categoria=categoria,
                     valor=valor)

    # add the new user to the database
    db.session.add(new_prato)
    db.session.commit()

    flash('Success')
    return redirect(url_for('menu'))


@app.route('/delete/<int:id>')
def delete(id):
    prato = Menu.query.get(id)
    db.session.delete(prato)
    db.session.commit()
    return redirect(url_for('menu'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    prato = Menu.query.get(id)

    if request.method == 'POST':
        prato.nome = request.form.get('nome')
        prato.categoria = request.form.get('categoria')
        prato.valor = request.form.get('valor')

        db.session.commit()

        return redirect(url_for('menu'))
    return render_template('edit.html', prato=prato)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
