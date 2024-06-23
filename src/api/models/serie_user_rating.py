from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
import datetime

from api import db


class SerieUserRating(db.Model):
    __tablename__ = "serie_user_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    serie_id = Column(Integer, ForeignKey("series.id"))
    rating = Column(String(15))
    date_rated = Column(DateTime, default=datetime.datetime.now)
    
    def __repr__(self):
        return "<SerieUserRating %r>" % self.id

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "serie_id": self.serie_id,
            "rating": self.rating,
            "date_rated": self.date_rated,
        }
