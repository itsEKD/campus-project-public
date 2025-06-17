from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from bson.objectid import ObjectId
from app import mongo
from mpesa_utils import stk_push
from datetime import datetime
import os
import stripe
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

guest_bp = Blueprint("guest", __name__, template_folder="templates")


@guest_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if session.get("role") != "guest":
        return redirect(url_for("auth.login"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    user_email = user.get("email")
    user_created = user.get("created_at", datetime.utcnow()).strftime("%Y-%m-%d")

    # Filters
    query = {"status": "approved"}
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    school = request.args.get("school", "").strip()

    if search:
        query["title"] = {"$regex": search, "$options": "i"}
    if department:
        query["department"] = {"$regex": department, "$options": "i"}
    if school:
        query["school"] = {"$regex": school, "$options": "i"}

    projects_cursor = mongo.db.projects.find(query).sort("created_at", -1)
    projects = list(projects_cursor)
    project_count = len(projects)

    return render_template(
        "guest/dashboard.html",
        projects=projects,
        project_count=project_count,
        user_email=user_email,
        user_created=user_created
    )


@guest_bp.route("/project/<project_id>")
def project_preview(project_id):
    if session.get("role") != "guest":
        return redirect(url_for("auth.login"))

    project = mongo.db.projects.find_one({"_id": ObjectId(project_id), "status": "approved"})
    if not project:
        return "Project not found or unavailable", 404

    return render_template("guest/project_preview.html", project=project)


@guest_bp.route("/purchase/<project_id>", methods=["GET", "POST"])
def purchase_project(project_id):
    if session.get("role") != "guest":
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")
    project = mongo.db.projects.find_one({"_id": ObjectId(project_id), "status": "approved"})
    if not project:
        return "Project not found", 404

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if "purchases" in user and str(project_id) in user["purchases"]:
        flash("You already purchased this project.")
        return redirect(url_for("guest.view_purchases"))

    # ✅ Get dynamic price or fallback to 50 KES
    amount = int(project.get("price", 50))

    if request.method == "POST":
        payment_method = request.form.get("payment_method")

        if payment_method == "mpesa":
            phone = request.form.get("phone")
            res = stk_push(phone, amount=amount, account_reference=str(project['_id']))
            if res.get("ResponseCode") == "0":
                flash("Mpesa payment request sent. Complete it on your phone.")
            else:
                flash(f"Mpesa payment failed: {res.get('errorMessage', 'Unknown error')}", "danger")
            return redirect(url_for("guest.purchase_project", project_id=project_id))

        elif payment_method == "stripe":
            try:
                # Stripe uses smallest currency unit (e.g. cents for USD)
                stripe_amount_usd_cents = int(amount / 150 * 100)  # approx conversion KES to USD

                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": project["title"],
                                "description": project.get("abstract", "")
                            },
                            "unit_amount": stripe_amount_usd_cents  # e.g. 500 = $5.00
                        },
                        "quantity": 1
                    }],
                    mode="payment",
                    success_url=f"{os.getenv('DOMAIN')}/guest/stripe_success/{project_id}",
                    cancel_url=f"{os.getenv('DOMAIN')}/guest/purchase/{project_id}",
                    metadata={
                        "user_id": str(user_id),
                        "project_id": str(project_id)
                    }
                )
                return redirect(checkout_session.url)
            except Exception as e:
                flash(f"Stripe error: {str(e)}", "danger")
                return redirect(url_for("guest.purchase_project", project_id=project_id))

        else:
            flash("Please select a valid payment method.", "warning")
            return redirect(url_for("guest.purchase_project", project_id=project_id))

    return render_template("guest/purchase.html", project=project)



@guest_bp.route("/stripe_success/<project_id>")
def stripe_success(project_id):
    if session.get("role") != "guest":
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if str(project_id) not in user.get("purchases", []):
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"purchases": str(project_id)}}
        )

    flash("Stripe payment successful! You can now access the project.")
    return redirect(url_for("guest.view_purchases"))


@guest_bp.route("/purchases")
def view_purchases():
    if session.get("role") != "guest":
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    purchased_ids = [ObjectId(pid) for pid in user.get("purchases", [])]
    projects = mongo.db.projects.find({"_id": {"$in": purchased_ids}})
    return render_template("guest/purchases.html", projects=projects)


@guest_bp.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if session.get("role") != "guest":
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        update_data = {
            "name": name,
            "email": email
        }
        if password:
            update_data["password"] = generate_password_hash(password)

        mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        session["email"] = email
        flash("Profile updated successfully.")
        return redirect(url_for("guest.edit_profile"))

    return render_template("guest/edit_profile.html", user=user)


@guest_bp.route("/mpesa_callback", methods=["POST"])
def mpesa_callback():
    data = request.get_json()

    try:
        result_code = data['Body']['stkCallback']['ResultCode']
        metadata = data['Body']['stkCallback'].get('CallbackMetadata', {}).get('Item', [])

        if result_code == 0:
            phone = next(item['Value'] for item in metadata if item['Name'] == 'PhoneNumber')
            reference = next(item['Value'] for item in metadata if item['Name'] == 'AccountReference')

            user = mongo.db.users.find_one({"phone": str(phone)})
            if user:
                mongo.db.users.update_one(
                    {"_id": user["_id"]},
                    {"$addToSet": {"purchases": reference}}
                )
                print(f"Payment success: Project {reference} added to user {user['email']}")
        else:
            print("Mpesa transaction failed or cancelled.")

    except Exception as e:
        print(f"Callback error: {e}")

    return {"ResultCode": 0, "ResultDesc": "Accepted"}
