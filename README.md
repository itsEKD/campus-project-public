# 🎓 Campus Project Management & Showcase App

A web-based system to manage and showcase academic projects within a university or college environment. Built for **students**, **lecturers**, **admins**, and **guests**, the app streamlines project submission, review, feedback, and purchase.

---

## 🚀 Purpose

To provide an organized, centralized platform where:
- Students can submit and manage their academic projects
- Lecturers can review, approve, and grade student work
- Admins can manage departments and users
- Guests can explore and purchase approved projects

---

## 🧑‍💻 User Roles & Permissions

### 👨‍🎓 Student
- Register with email, **admission number**, and department
- Upload/edit individual or team-based projects
- Upload demo video (MP4/WebM)
- View lecturer feedback and grades

### 👩‍🏫 Lecturer
- Register with email, **service number**, and department
- View assigned department projects
- Comment, approve/reject, and assign grades

### 🛠️ Admin
- Register with email and **service number**
- Create and manage departments
- Assign lecturers to departments
- Register/manage users (students, lecturers, guests)
- View analytics
- ❌ Cannot approve or grade projects

### 👤 Guest
- Register with email
- Browse/search approved projects
- Purchase/download projects

---

## 🏛️ Department-Based Classification

- Projects are grouped under departments
- Students and lecturers are assigned to departments
- Admins manage department creation and assignments

---

## 📦 Project Types

### Single Project
- Submitted and owned by one student

### Team Project
- Collaboratively managed by 2–5 students
- Team leader has main editing rights

### Every project includes:
- Title, description (via Quill.js)
- Tags/keywords
- File uploads (PDF/ZIP)
- Video demo
- Status: `Pending`, `Approved`, `Rejected`, `Graded`
- Lecturer feedback
- Optional guest ratings

---

## 🔐 Registration Requirements

| Role     | Fields Required                        |
|----------|----------------------------------------|
| Admin    | Email, **service number**, password     |
| Lecturer | Email, **service number**, department, password |
| Student  | Email, **admission number**, department, password |
| Guest    | Email, password                        |

---

## 💡 Features Summary

### 👨‍🎓 Student Panel
- Upload/edit project files
- Join/create team project
- Upload demo video
- Track status & feedback

### 👩‍🏫 Lecturer Panel
- View projects in assigned departments
- Approve/reject and grade projects
- Comment and provide feedback

### 🛠️ Admin Panel
- Manage users & departments
- Assign lecturers
- View platform-wide statistics

### 👤 Guest Panel
- Register/login
- Browse/search projects
- Purchase and download files

---

## 📈 Optional Enhancements

- 🔔 Email notifications on status changes
- ⭐ Guest ratings
- 📄 PDF project preview in browser
- 📊 Admin analytics dashboard
- 📁 Export reports (PDF format)
- 🔄 Project version tracking

---

## ⚙️ Tech Stack

| Layer     | Technology         |
|-----------|--------------------|
| Backend   | Flask (Python)     |
| Frontend  | HTML, Bootstrap, JS, Jinja2 |
| Rich Text | Quill.js           |
| Database  | MongoDB Atlas      |
| Media     | Flask-Uploads / GridFS |
| Auth      | Flask-Login, Flask-WTF |
| Payments  | Stripe (guest purchases) |
| Optional  | Flask-SocketIO (real-time commenting) |

---

## 📌 Development Plan

1. Scaffold folder structure and configure Flask app
2. Implement authentication system (4 user roles)
3. Set up department management & project classification
4. Develop:
   - Admin dashboard
   - Lecturer panel
   - Student portal
   - Guest shopping interface
5. Add project workflows:
   - Upload → Review → Approval → Grading → Purchase
6. Finalize UI with Bootstrap & JS enhancements
7. Integrate optional features and deploy

---

## 📁 Folder Structure Overview

```bash
campus_proj_app/
├── auth/         # Login/registration for all roles
├── admin/        # Admin dashboard & controls
├── student/      # Student project panel
├── lecturer/     # Lecturer grading/review panel
├── guest/        # Guest browsing/purchasing
├── static/uploads/
│   ├── videos/
│   ├── project_files/
├── templates/
├── config.py
├── models/
├── utils/
├── requirements.txt
└── wsgi.py
```

---

## 💬 Contact & Contribution

Have ideas or want to contribute? Open issues or submit pull requests. Let’s make student project sharing better across campuses.

---
