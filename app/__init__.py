from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from dotenv import load_dotenv
import os

mongo = PyMongo()
bcrypt = Bcrypt()
mail = Mail()

def create_app():
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == "True"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")


    # Init extensions
    mongo.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)



    # Register Blueprints
    from app.auth import auth_bp
    from app.student import student_bp
    from app.lecturer import lecturer_bp
    from app.guest import guest_bp
    from app.main import main_bp  # ✅ for homepage
    from app.admin import admin_bp
    
    
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(lecturer_bp, url_prefix="/lecturer")
    app.register_blueprint(guest_bp, url_prefix="/guest")
    app.register_blueprint(main_bp)  # Homepage, no prefix
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
