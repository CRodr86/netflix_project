from sqlalchemy import Column, Integer, String, Float

from api import db


class Movie(db.Model):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True)
    title = Column(String(300))
    director = Column(String(300))
    cast = Column(String(1000))
    country = Column(String(300))
    date_added = Column(String(100))
    age_rating = Column(String(10))
    listed_in = Column(String(300))
    description = Column(String(2000))
    imdb_id = Column(String(20))
    is_adult = Column(Integer)
    start_year = Column(Integer)
    runtime_minutes = Column(Integer)
    genres = Column(String(300))
    average_rating = Column(Float)
    num_votes = Column(Integer)
    spoken_languages = Column(String(50))
    original_language = Column(String(50))
    poster_url = Column(String(300))
    youtube_trailers = Column(String(1000))
    popularity = Column(Float)
    user_ratings = db.relationship("MovieUserRating", backref="movie", lazy=True)

    def __repr__(self):
        return "<Movie %r>" % self.title

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "director": self.director,
            "cast": self.cast,
            "country": self.country,
            "date_added": self.date_added,
            "age_rating": self.age_rating,
            "listed_in": self.listed_in,
            "description": self.description,
            "imdb_id": self.imdb_id,
            "is_adult": self.is_adult,
            "start_year": self.start_year,
            "runtime_minutes": self.runtime_minutes,
            "genres": self.genres,
            "average_rating": self.average_rating,
            "num_votes": self.num_votes,
            "spoken_languages": self.spoken_languages,
            "original_language": self.original_language,
            "poster_url": self.poster_url,
            "youtube_trailers": self.youtube_trailers,
            "popularity": self.popularity,
        }
