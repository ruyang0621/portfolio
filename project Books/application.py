import os, json
import requests

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from helpers import apology, login_required
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
 
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Check for environment variable
if not os.getenv("GOODREADS_KEY"):
    raise RuntimeError("GOODREADS_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/homepage")
@login_required
def homepage():
    name = db.execute("SELECT user_name FROM users WHERE personal_id = :personal_id",
                      {"personal_id": session["user_id"]}).fetchone()
    review_detail = db.execute("SELECT b.title, b.isbn, r.review, r.rate, r.user_name FROM reviewed r JOIN books b ON r.isbn = b.isbn ORDER BY r.id DESC LIMIT 5").fetchall()
    length = len(review_detail)
    return render_template("homepage.html", name=name, review_detail=review_detail, length=length)


@app.route("/login", methods=["POST", "GET"])
def login():
    """Log user in"""
    if request.method == "GET":
        return render_template("login.html")
    else:
        if not request.form.get("username"):
            return apology("must provide username", 403)
        if not request.form.get("password"):
            return apology("must provide password", 403)
        rows = db.execute("SELECT password, personal_id FROM users WHERE user_name= :username",
                         {"username": request.form.get("username")}).fetchall()
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology ("invalid username and/or password", 403)

        session["user_id"] = rows[0]["personal_id"]
        return redirect("/homepage")

@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
    """Search Books"""
    if request.method == "GET":
        return render_template("search.html")
    else:
        if not request.form.get("select_search"):
            return apology("please select ISBN/TITLE/AUTHOR", 403)
        if not request.form.get("keyword"):
            return apology("must provide keyword(ISBN/TITLE/AUTHOR)", 403)
        if request.form.get("select_search") == "isbn":
            book_rows = db.execute("SELECT * FROM books WHERE LOWER(isbn) LIKE :isbn",
                              {"isbn": "%"+request.form.get("keyword").lower()+"%"}).fetchall()
            return render_template("result.html", book_rows=book_rows, length=len(book_rows))
        if request.form.get("select_search") == "title":
            book_rows = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE :title",
                              {"title": "%"+request.form.get("keyword").lower()+"%"}).fetchall()
            return render_template("result.html", book_rows=book_rows, length=len(book_rows))
        if request.form.get("select_search") == "author":
            book_rows = db.execute("SELECT * FROM books WHERE LOWER(author) LIKE :author",
                              {"author": "%"+request.form.get("keyword").lower()+"%"}).fetchall()
            return render_template("result.html", book_rows=book_rows, length=len(book_rows))


@app.route("/detail", methods=["GET", "POST"])
@login_required
def detail():
    if request.method == "GET":
        """show book detail"""
        if not request.args.get("isbn"):
            return apology ("oops~wrong route", 404)
        else:
            key = os.getenv("GOODREADS_KEY")
            detail_isbn = request.args.get("isbn")
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": detail_isbn})
            book_detail = res.json()
            id_book = db.execute("SELECT id FROM books WHERE isbn= :isbn",
                            {"isbn": detail_isbn}).fetchone()
            name_book = db.execute("SELECT title FROM books WHERE isbn= :isbn",
                            {"isbn": detail_isbn}).fetchone()
            review_detail = db.execute("SELECT * FROM reviewed WHERE isbn = :isbn ORDER BY ID DESC", 
                                           {"isbn": detail_isbn}).fetchall()
            length = len(review_detail)
            return render_template("detail.html", book_detail=book_detail, id=id_book, name_book=name_book, review_detail=review_detail, length=length)
    if request.method == "POST":
        if not request.form.get("review") or not request.form.get("select_search"):
            return apology ("missing rate / review", 403)
        else:
            key = os.getenv("GOODREADS_KEY")
            detail_isbn = request.form.get("isbnid")
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": detail_isbn})
            book_detail = res.json()
            id_book = db.execute("SELECT id FROM books WHERE isbn= :isbn",
                            {"isbn": detail_isbn}).fetchone()
            name_book = db.execute("SELECT title FROM books WHERE isbn= :isbn",
                            {"isbn": detail_isbn}).fetchone()
            review = request.form.get("review")
            rate = request.form.get("select_search")
            exist_id = db.execute("SELECT * FROM reviewed WHERE personal_id = :personal_id AND isbn = :isbn",
                                  {"personal_id": session["user_id"], "isbn": detail_isbn}).fetchone()
            print(exist_id)
            if not exist_id:
                user_name = db.execute("SELECT user_name FROM users WHERE personal_id = :personal_id",
                                       {"personal_id": session["user_id"], "isbn": detail_isbn}).fetchone()
                db.execute("INSERT INTO reviewed (personal_id, isbn, review, rate, user_name) VALUES (:personal_id, :isbn, :review, :rate, :user_name)", 
                            {"personal_id": session["user_id"], "isbn": detail_isbn, "review": review, "rate": rate, "user_name": user_name[0]})
                db.commit()
                review_detail = db.execute("SELECT * FROM reviewed WHERE isbn = :isbn ORDER BY id DESC", 
                                           {"isbn": detail_isbn}).fetchall()
                length = len(review_detail)
                return render_template("detail.html", book_detail=book_detail, id=id_book, name_book=name_book, review_detail = review_detail, length=length)
            else:
                return apology ("review has existed", 403)
            
        
        
@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/check", methods=["POST", "GET"])
def check():
    if request.method == "GET":
        return "false"
    else:
        rows = db.execute("SELECT * FROM users WHERE user_name = :username",
                   {"username": request.form.get("username")}).fetchall()
        if not request.form.get("username"):
            return "false"
        elif len(rows) == 1:
            return "false1"
        elif not request.form.get("password"):
            return "false2"
        elif request.form.get("password") != request.form.get("password_confirm"):
            return "false3"
        else:
            return "success"


@app.route("/register", methods=["GET", "POST"])
def register():
    """new user register"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        user_name = request.form.get("username")
        password = request.form.get("password")
        hash_p = generate_password_hash(password, method='pbkdf2:sha256', salt_length=len(password))
        db.execute("INSERT INTO users (user_name, password) VALUES (:username, :password)", 
                   {"username": user_name, "password": hash_p})
        db.commit()
        rows = db.execute("SELECT * FROM users WHERE user_name = :username",
                          {"username": request.form.get("username")}).fetchone()
        session["user_id"] = rows["personal_id"]
        return redirect("/homepage")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
