from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    national_id = db.Column(db.String(10), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    birthdate = db.Column(db.String(10))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=0)