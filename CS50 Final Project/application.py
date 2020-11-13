import os, json
import requests
import time

from newsapi import NewsApiClient
from datetime import date, datetime

from flask import Flask, render_template, url_for, flash, redirect, request, session
from forms import RegistrationForm, LoginForm
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from helpers import login_required
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

#set secret_key
app.config['SECRET_KEY'] = '87225b1a6ffa540b0b93ef6f2ca798b1'

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Set up NewsApi
newsapi = NewsApiClient(api_key='bb2e5fb13c6a4307bf87765969914c80')


@app.route("/")
def index():
    session.clear()
    return render_template('index.html')


@app.route("/home")
@login_required
def home():
    top_headlines = newsapi.get_top_headlines(language='en', country='us')
    print(top_headlines)
    return render_template('home.html', title='Home', top_headlines=top_headlines)

@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        
        flash(f'Account created for { form.username.data }! You are now able to log in.', 'sucess')
        hash_p = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=len(form.password.data))
        db.execute("INSERT INTO notebook.users (username, password, email) VALUES (:username, :password, :email)", 
                   {"username": form.username.data, "password": hash_p, "email": form.email.data})
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        rows = db.execute("SELECT password, id FROM notebook.users WHERE email = :email",
                          {"email": form.email.data}).fetchall()
        print("hereherehere")
        print("hereherehere")
        print("hereherehere")
        print("hereherehere")
        print(len(rows))
        print("hereherehere")
        print("hereherehere")
        print("hereherehere")
        print("hereherehere")
        if len(rows) == 1 and check_password_hash(rows[0]["password"], form.password.data):
            flash('You have been logged in!', 'sucess')
            session["user_id"] = rows[0]["id"]

            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    if request.method == "GET":
        return render_template('search.html', title='Search')
    else:
        ts = time.time()
        db.execute("INSERT INTO notebook.history (user_id, keyword, d_start, d_end, mydate) VALUES (:user_id, :keyword, :d_start, :d_end, :mydate)", 
                   {"user_id": session["user_id"], "keyword": request.form.get("keyword"), 
                    "d_start": request.form.get("trip-start"), "d_end": request.form.get("trip-end"), "mydate": datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')})
        db.commit()
        all_articles = newsapi.get_everything(q=request.form.get("keyword"),
                                              from_param=request.form.get("trip-start"),
                                              to=request.form.get("trip-end"),
                                              language='en',
                                              page=1,
                                              sort_by='popularity')
        return render_template("result.html", title="Result", all_articles=all_articles, length=len(all_articles['articles']))


@app.route("/history")
@login_required
def history():
    rows = db.execute("SELECT * FROM notebook.history WHERE user_id = :user_id", {"user_id": session["user_id"]}).fetchall()
    return render_template("history.html", rows=rows, length=len(rows))


@app.route("/logout")
def logout():
    session.clear()
    return render_template('index.html')


@app.route("/check", methods=["POST"])
def check():
    form = RegistrationForm()
    row1 = db.execute("SELECT * FROM notebook.users WHERE username = :username",
                      {"username": form.username.data}).fetchall()
    row2 = db.execute("SELECT * FROM notebook.users WHERE email = :email",
                      {"email": form.email.data}).fetchall()
    if  len(row1) == 1:
        return "false"
    elif len(row2) == 1:
        return "false"
    else:
        return "success"


