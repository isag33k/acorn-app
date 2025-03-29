import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "a secret key"

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"options": "-c search_path=acorn_schema,public"}
}
# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Set search path explicitly for this session
    db.session.execute(text("SET search_path TO acorn_schema, public;"))
    db.session.commit()
    
    # Import models and create tables
    import models
    db.create_all()
    print("Database tables created successfully in acorn_schema.")
