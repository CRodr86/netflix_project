from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from api import db


class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    password = Column(String(240))
    age = Column(Integer)
    movies_ratings = relationship("MovieUserRating", backref="user", lazy=True)
    series_ratings = relationship("SerieUserRating", backref="user", lazy=True)
    favorite_genres = Column(String(300))

    def __repr__(self):
        return "<User %r>" % self.username

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "age": self.age,
            "favorite_genres": self.favorite_genres,
        }
