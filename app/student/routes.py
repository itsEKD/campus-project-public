from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app import mongo
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from bson.objectid import ObjectId


student_bp = Blueprint("student", __name__, template_folder="templates")

UPLOAD_FOLDER = "app/static/uploads/projects"
ALLOWED_EXTENSIONS = {'pdf'}

VIDEO_UPLOAD_FOLDER = "app/static/uploads/project_videos"
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

@student_bp.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    student_email = session['email']
    db = mongo.db

    # Fetch all projects (single or team) where the user is:
    # - the uploader (for individual project)
    # - OR a member of a team project
    projects_cursor = db.projects.find({
        "$or": [
            {"student_email": student_email},
            {"team_members": student_email}
        ]
    })

    projects = []
    for project in projects_cursor:
        # Ensure fallback values
        project['is_team_project'] = project.get('is_team_project', False)
        project['team_members'] = project.get('team_members', [])
        project['leader_email'] = project.get('leader_email', project.get('student_email'))  # leader or individual owner
        projects.append(project)

    return render_template('student/dashboard.html', projects=projects, current_user={"email": student_email})


@student_bp.route("/upload", methods=["GET", "POST"])
def upload_project():
    if "user_id" not in session or session.get("role") != "student":
        flash("Unauthorized access.")
        return redirect(url_for("auth.login"))

    student = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if not student:
        flash("Student not found.")
        return redirect(url_for("auth.login"))

    department = student.get("department")
    school = student.get("school")

    # Check if already in a team project
    existing_team = mongo.db.projects.find_one({
        "is_team_project": True,
        "team_members": {"$in": [student["email"]]}
    })
    if existing_team:
        flash("You are already part of a team project.")
        return redirect(url_for("student.dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        abstract = request.form.get("abstract")
        is_team_project = request.form.get("is_team_project") == "on"
        member_emails = request.form.getlist("member_emails")

        # Required files
        file = request.files.get("project_file")
        video = request.files.get("demo_video")

        # Clean inputs
        member_emails = [email.strip().lower() for email in member_emails if email.strip()]
        all_members = list(set([student["email"]] + member_emails))

        if not title or not abstract or not file:
            flash("Title, abstract, and project file are required.")
            return redirect(request.url)

        if is_team_project:
            if len(all_members) > 5:
                flash("Team projects must have at most 5 members (including yourself).")
                return redirect(request.url)

            # Validate members
            valid_users = list(mongo.db.users.find({
                "email": {"$in": member_emails},
                "role": "student",
                "department": department
            }))
            if len(valid_users) != len(member_emails):
                flash("Some team members are invalid or not from your department.")
                return redirect(request.url)

            # Ensure none are already in a team project
            conflict = mongo.db.projects.find_one({
                "is_team_project": True,
                "team_members": {"$in": member_emails}
            })
            if conflict:
                flash("One or more invited members are already in another team project.")
                return redirect(request.url)

        # Save project PDF
        pdf_path = None
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            pdf_path = os.path.join("static/uploads/projects", filename)
            file.save(os.path.join("app", pdf_path))
        else:
            flash("Invalid PDF file.")
            return redirect(request.url)

        # Save optional demo video
        video_path = None
        if video and allowed_video(video.filename):
            video_filename = f"{uuid.uuid4()}_{secure_filename(video.filename)}"
            video_path = os.path.join("static/uploads/project_videos", video_filename)
            video.save(os.path.join("app", video_path))

        # Final project object
        project_data = {
            "title": title,
            "abstract": abstract,
            "department": department,
            "school": school,
            "pdf_path": pdf_path,
            "video_path": video_path,
            "status": "pending",
            "submitted_at": datetime.utcnow(),
            "is_team_project": is_team_project
        }

        if is_team_project:
            project_data["team_members"] = all_members
            project_data["leader_email"] = student["email"]
        else:
            project_data["student_id"] = student["_id"]
            project_data["student_email"] = student["email"]

        mongo.db.projects.insert_one(project_data)
        flash("Project submitted successfully!")
        return redirect(url_for("student.dashboard"))

    return render_template("student/upload_project.html", student=student)




@student_bp.route("/edit/<project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Unauthorized access.")
        return redirect(url_for("auth.login"))

    project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        flash("Project not found.")
        return redirect(url_for("student.dashboard"))

    if str(project["student_id"]) != session["user_id"]:
        flash("You are not authorized to edit this project.")
        return redirect(url_for("student.dashboard"))

    if project.get("status") == "approved":
        flash("Approved projects cannot be edited.")
        return redirect(url_for("student.dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        abstract = request.form.get("abstract")

        update_data = {
            "title": title,
            "abstract": abstract,
            "updated_at": datetime.utcnow()
        }

        # Handle PDF upload
        file = request.files.get("project_file")
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            pdf_path = os.path.join("static/uploads/projects", filename)
            file.save(os.path.join("app", pdf_path))
            update_data["pdf_path"] = pdf_path

        # Handle video upload
        video = request.files.get("demo_video")
        if video and allowed_video(video.filename):
            video_filename = f"{uuid.uuid4()}_{secure_filename(video.filename)}"
            video_path = os.path.join("static/uploads/project_videos", video_filename)
            video.save(os.path.join("app", video_path))
            update_data["video_path"] = video_path

        mongo.db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": update_data}
        )
        flash("Project updated successfully.")
        return redirect(url_for("student.dashboard"))

    return render_template("student/edit_project.html", project=project)


@student_bp.route("/delete/<project_id>", methods=["POST"])
def delete_project(project_id):
    project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for("student.dashboard"))

    # Check ownership
    if str(project["student_id"]) != session["user_id"]:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("student.dashboard"))

    # Prevent deletion if approved
    if project.get("status") == "approved":
        flash("Approved projects cannot be deleted.", "warning")
        return redirect(url_for("student.dashboard"))

    mongo.db.projects.delete_one({"_id": ObjectId(project_id)})
    flash("Project deleted successfully.", "success")
    return redirect(url_for("student.dashboard"))

@student_bp.route("/project/<project_id>/react", methods=["POST"])
def react_to_project(project_id):
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    reaction_type = request.form.get("reaction")

    if reaction_type not in ["like", "love", "clap"]:
        flash("Invalid reaction.")
        return redirect(url_for("student.view_project_comments", project_id=project_id))

    mongo.db.reactions.update_one(
        {"project_id": ObjectId(project_id), "user_id": ObjectId(user_id)},
        {"$set": {"reaction": reaction_type}},
        upsert=True
    )

    return redirect(url_for("student.view_project_comments", project_id=project_id))


@student_bp.route("/project/<project_id>/comments", methods=["GET", "POST"])
def view_project_comments(project_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Unauthorized access.")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        flash("User not found.")
        return redirect(url_for("auth.login"))

    project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        flash("Project not found.")
        return redirect(url_for("student.dashboard"))

    # Handle comment submission
    if request.method == "POST" and "comment" in request.form:
        comment_text = request.form["comment"].strip()
        if comment_text:
            mongo.db.comments.insert_one({
                "project_id": ObjectId(project_id),
                "user_id": ObjectId(user_id),
                "user_email": user["email"],
                "user_name": user.get("name", ""),
                "comment": comment_text,
                "timestamp": datetime.utcnow()
            })
            flash("Comment added successfully!")
        return redirect(request.url)

    # Fetch comments
    comments = list(mongo.db.comments.find({"project_id": ObjectId(project_id)}).sort("timestamp", -1))

    # Fetch reactions count
    reactions_data = mongo.db.reactions.find({"project_id": ObjectId(project_id)})
    reaction_counts = {"like": 0, "love": 0, "clap": 0}
    user_reacted = None

    for reaction in reactions_data:
        reaction_type = reaction["reaction"]
        if reaction_type in reaction_counts:
            reaction_counts[reaction_type] += 1
        if reaction["user_id"] == ObjectId(user_id):
            user_reacted = reaction_type

    return render_template(
        "student/view_project_comments.html",
        project=project,
        comments=comments,
        reaction_counts=reaction_counts,
        user_reacted=user_reacted
    )