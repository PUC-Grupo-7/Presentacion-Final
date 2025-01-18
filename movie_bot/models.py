# movie_bot/models.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db import db
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    favorite_genre = db.Column(db.String(50), nullable=True)
    disliked_genre = db.Column(db.String(50), nullable=True)
    # Nueva columna para la región del usuario
    region = db.Column(db.String(5), nullable=True, default="US")

    messages = db.relationship('Message', backref='user', lazy=True)
    recommendations = db.relationship('Recommendation', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)  # 'user' o 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Message {self.id} by {self.author} at {self.timestamp}>"

class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)  # ID de TMDB
    movie_title = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Recommendation {self.movie_title} (ID: {self.movie_id}) for User {self.user_id}>"
