import os
import logging
from datetime import datetime, timedelta
from flask import Flask, session, g, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize database base class
class Base(DeclarativeBase):
    pass

# Create the db instance
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "test_key")
csrf = CSRFProtect(app)



# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add the user loader function
@login_manager.user_loader
def load_user(user_id):
    try:
        # Import User model inside the function to avoid circular imports
        from models import User
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

# Initialize the app with the extension
db.init_app(app)

# Configure uploads directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Newline to <br> filter for Jinja templates
@app.template_filter('nl2br')
def nl2br_filter(s):
    if s:
        return s.replace('\n', '<br>')
    return s

# Utility processor for Jinja templates
@app.context_processor
def utility_processor():
    from flask import session
    
    def nl2br(value):
        if value:
            return value.replace('\n', '<br>')
        return value
    
    return dict(nl2br=nl2br)

# Theme processor for Jinja templates
@app.context_processor
def theme_processor():
    """Provide the current theme to all templates"""
    try:
        from models import AppSettings
        current_theme = AppSettings.get_current_theme()
        return {'theme': current_theme}
    except Exception as e:
        logger.error(f"Error loading theme: {str(e)}")
        return {'theme': 'default'}

# Initialize the database tables
with app.app_context():
    # Import models
    import models

    try:
        # Create all tables
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        logger.error(f"Database initialization error: {str(e)}")

    # Import routes to register them
    try:
        import routes
        print("Routes imported successfully")
    except Exception as e:
        print(f"Error importing routes: {str(e)}")
        logger.error(f"Routes import error: {str(e)}")

# Simple test route
@app.route('/test')
def test():
    return "<h1>Hello ACORN!</h1><p>The test route is working with SQLAlchemy.</p>"

# Main entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
