from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
schools_collection = db.schools

# Define departments to add to each school
department_updates = {
    "School of Science, Engineering and Technology": [
        "Information Technology", "Computer Science", "BBIT", "Forensics", "BMIT"
    ],
    "School of Education and Social Sciences": [
        "Education", "Sociology", "Psychology", "Political Science"
    ],
    "School of Business and Economics": [
        "Accounting", "Finance", "Marketing", "Human Resource", "Entrepreneurship"
    ],
    "School of Law": [
        "Commercial Law", "Criminal Law", "International Law"
    ],
    "School of Health and Nursing Sciences": [
        "Nursing", "Public Health", "Pharmacy"
    ],
    "School of Theology": [
        "Biblical Studies", "Pastoral Studies"
    ],
    "School of Music": [
        "Performance", "Music Theory", "Composition"
    ]
}

# Update each school with its departments
for school_name, departments in department_updates.items():
    result = schools_collection.update_one(
        {"school": school_name},
        {"$set": {"departments": departments}}
    )
    if result.modified_count:
        print(f"✅ Updated departments for: {school_name}")
    else:
        print(f"⚠️ No match or already up-to-date: {school_name}")

client.close()
