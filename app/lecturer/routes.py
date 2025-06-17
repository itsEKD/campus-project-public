from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from app import mongo
from bson.objectid import ObjectId

lecturer_bp = Blueprint("lecturer", __name__, template_folder="templates")


@lecturer_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "lecturer":
        flash("Access denied.")
        return redirect(url_for("auth.login"))

    lecturer = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    departments = lecturer.get("departments")  # ✅ use plural

    if not departments:
        flash("No departments assigned. Please contact admin.")
        return redirect(url_for("auth.login"))

    # ✅ Fetch all projects where department is in lecturer's departments list
    projects = list(mongo.db.projects.find({"department": {"$in": departments}}))

    return render_template("lecturer/dashboard.html", projects=projects)



@lecturer_bp.route("/update/<project_id>", methods=["POST"])
def update_project(project_id):
    if "user_id" not in session or session.get("role") != "lecturer":
        flash("Access denied.")
        return redirect(url_for("auth.login"))

    status = request.form.get("status")
    grade = request.form.get("grade")
    comment = request.form.get("comment")

    mongo.db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {
            "status": status,
            "grade": grade,
            "lecturer_comment": comment
        }}
    )

    flash("Project updated.")
    return redirect(url_for("lecturer.dashboard"))
