from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

# Movies endpoint

API_KEY = "API KEY"
search_movies_endpoint = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&language=en-US&query="

# create the extension
db = SQLAlchemy()

# create the app
app = Flask(__name__)

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///favorite_movies.db"

# initialize the app with the extension
db.init_app(app)


# DB table as code (model)
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String, nullable=False)
    img_url = db.Column(db.String, nullable=False)


# Helper functions
def get_movie(title):
    return db.session.execute(db.select(Movie).filter_by(title=title)).scalar()


def rank_movies(watch_list):
    movies = [movie for movie in watch_list]
    movies = movies[::-1]

    i = 1
    for movie in movies:
        movie.ranking = i
        i += 1
    db.session.commit()
    return movies


# Routes
@app.route("/")
def home():
    db.create_all()
    watch_list = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars()
    movies = rank_movies(watch_list)
    return render_template("index.html", movies=movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        query = search_movies_endpoint + request.form.get("title").lower()
        response = requests.get(url=query)
        if response.status_code == 200:
            movies = response.json()['results']
            return render_template("search.html", movies=movies)
    return render_template("add.html")


@app.route("/add/<int:id>")
def add_to_db(id):
    get_movie_endpoint = f"https://api.themoviedb.org/3/movie/{id}?api_key={API_KEY}&language=en-US"
    response = requests.get(url=get_movie_endpoint)
    if response.status_code == 200:
        print(response.json())
        movie = response.json()
        new_movie = Movie(
            title=movie["title"],
            year=movie["release_date"][0:5],
            description=movie['overview'],
            rating=0,
            ranking=0,
            review="None",
            img_url=f"https://image.tmdb.org/t/p/w500/{movie['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("update", title=new_movie.title))
    return redirect(url_for("search.html"))


@app.route("/details/<title>")
def movie_details(title):
    movie = get_movie(title)
    return render_template("details.html", movie=movie)


@app.route("/update/<title>", methods=["GET", "POST"])
def update(title):
    if request.method == "POST":
        movie = get_movie(title)
        if request.form.get('new_rating'):
            movie.rating = request.form['new_rating']
        if request.form.get('movie_review'):
            movie.review = request.form['movie_review']
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("update.html", title=title)


@app.route("/delete/<title>", methods=["GET"])
def delete_movie(title):
    movie = get_movie(title)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))



