from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
import datetime

from api import db


class MovieUserRating(db.Model):
    __tablename__ = "movie_user_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    rating = Column(String(15))
    date_rated = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return "<MovieUserRating %r>" % self.id

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "rating": self.rating,
            "date_rated": self.date_rated,
        }
