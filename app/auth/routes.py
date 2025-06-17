from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import mongo, bcrypt, mail
import base64
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message


auth_bp = Blueprint("auth", __name__, template_folder="templates")



# Create token generator
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def send_verification_email(email):
    token = generate_confirmation_token(email)
    confirm_url = url_for('auth.verify_email', token=token, _external=True)
    msg = Message('Verify Your Email', sender=current_app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f"Welcome! Please verify your email by clicking this link:\n{confirm_url}\n\nIf you did not register, ignore this email."
    mail.send(msg)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        role_id = request.form.get("role_id")
        school = request.form.get("school")
        department = request.form.get("department")

        # Basic validation
        if not email or not password or not role or not role_id:
            flash("All fields are required.")
            return redirect(url_for("auth.register"))

        if mongo.db.users.find_one({"email": email}):
            flash("Email already registered.")
            return redirect(url_for("auth.register"))

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        # Construct user data
        user_data = {
            "email": email,
            "password": hashed_pw,
            "role": role,
            "role_id": role_id,
            "verified": False,
        }

        if role == "student":
            if not school or not department:
                flash("Please select both school and department.")
                return redirect(url_for("auth.register"))
            user_data["school"] = school
            user_data["department"] = department

        elif role == "lecturer":
            if school:
                user_data["school"] = school

        mongo.db.users.insert_one(user_data)
        send_verification_email(email)

        flash("Registration successful! Please check your email to verify your account.")
        return redirect(url_for("auth.login"))

    schools = list(mongo.db.schools.find())
    return render_template("auth/register.html", schools=schools)






@auth_bp.route('/verify/<token>')
def verify_email(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=3600)
    except Exception:
        flash("The confirmation link is invalid or has expired.")
        return redirect(url_for("auth.login"))

    user = mongo.db.users.find_one({"email": email})

    if user and not user.get("verified"):
        mongo.db.users.update_one({"email": email}, {"$set": {"verified": True}})
        flash("Email verified! You can now log in.")
    else:
        flash("Account already verified or does not exist.")

    return redirect(url_for("auth.login"))



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = mongo.db.users.find_one({"email": email})

        if user and bcrypt.check_password_hash(user["password"], password):
            if not user.get("verified"):
                flash("Please verify your email before logging in.")
                return redirect(url_for("auth.login"))

            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash("Login successful!")

            # Redirect based on role
            if user["role"] == "student":
                return redirect(url_for("student.dashboard"))
           
            elif user["role"] == "lecturer":
                return redirect(url_for("lecturer.dashboard"))
            
            elif user["role"] == "admin":  
                return redirect(url_for("admin.dashboard"))
            
            elif user["role"] == "guest":
                return redirect(url_for("guest.dashboard"))
            else:
                return redirect(url_for("main.home"))

        flash("Invalid email or password.")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))



