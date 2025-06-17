from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bson.objectid import ObjectId
from app import mongo  # since you're importing mongo from app


admin_bp = Blueprint("admin", __name__, template_folder="templates")

@admin_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Unauthorized access.")
        return redirect(url_for("auth.login"))

    # Fetch summary data for dashboard display (customize as needed)
    total_users = mongo.db.users.count_documents({})
    total_students = mongo.db.users.count_documents({"role": "student"})
    total_lecturers = mongo.db.users.count_documents({"role": "lecturer"})
    total_schools = mongo.db.schools.count_documents({})
    
    return render_template("admin/dashboard.html", 
                           total_users=total_users,
                           total_students=total_students,
                           total_lecturers=total_lecturers,
                           total_schools=total_schools)




@admin_bp.route("/assign_departments", methods=["GET", "POST"])
def assign_departments():
    # Fetch all lecturers
    lecturers = list(mongo.db.users.find({"role": "lecturer"}))

    # Fetch all schools
    schools = list(mongo.db.schools.find())

    if request.method == "POST":
        lecturer_id = request.form.get("lecturer_id")
        selected_departments = request.form.getlist("departments[]")
        school_name = request.form.get("school")

        if lecturer_id and selected_departments:
            mongo.db.users.update_one(
                {"_id": ObjectId(lecturer_id)},
                {
                    "$set": {
                        "departments": selected_departments,
                        "school": school_name
                    }
                }
            )
            flash("Departments assigned successfully.")
            return redirect(url_for("admin.assign_departments"))
        else:
            flash("Please select a lecturer and at least one department.")

    return render_template(
        "admin/assign_departments.html",
        lecturers=lecturers,
        schools=schools
    )



@admin_bp.route("/manage-departments", methods=["GET", "POST"])
def add_department():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Unauthorized access.")
        return redirect(url_for("auth.login"))

    schools = list(mongo.db.schools.find())

    if request.method == "POST":
        school_id = request.form.get("school_id")
        new_department = request.form.get("department_name")

        if not school_id or not new_department:
            flash("All fields are required.")
            return redirect(url_for("admin.add_department"))

        # Add department to school (if not exists)
        mongo.db.schools.update_one(
            {"_id": ObjectId(school_id)},
            {"$addToSet": {"departments": new_department}}  # No duplicates
        )

        flash("Department added successfully.")
        return redirect(url_for("admin.add_department"))

    return render_template("admin/manage_departments.html", schools=schools)

