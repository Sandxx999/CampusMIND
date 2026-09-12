import sqlite3
import random
import os
import sys

# Ensure backend path is included
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import settings

DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Aditya", "Sneha", "Vikram", "Kavya", "Rahul", "Neha",
    "Siddharth", "Pooja", "Arjun", "Ishita", "Karan", "Riya", "Dev", "Divya", "Varun", "Meera",
    "Yash", "Shreya", "Tanmay", "Anushka", "Nikhil", "Simran", "Abhinav", "Aditi", "Manish", "Swati",
    "Vivek", "Preeti", "Saurabh", "Tarun", "Aakash", "Deepika", "Harsh", "Ritika", "Gaurav", "Nisha",
    "Pranav", "Rashmi", "Sameer", "Bhavna", "Kunal", "Tanya", "Akshay", "Monika", "Chirag", "Payal",
    "Rajesh", "Sonam", "Alok", "Kirti", "Mayank", "Shikha", "Nitin", "Richa", "Sanjay", "Komal",
    "Ashish", "Anjali", "Dinesh", "Pallavi", "Gautam", "Jyoti", "Hemant", "Nandini", "Lokesh", "Kavita",
    "Mohit", "Poonam", "Pankaj", "Rachna", "Rakesh", "Sangeeta", "Sachin", "Sunita", "Tushar", "Vandana",
    "Vijay", "Varsha", "Yogesh", "Archana", "Deepak", "Geeta", "Kamal", "Lata", "Mukesh", "Nirmala",
    "Pawan", "Rekha", "Satish", "Sarita", "Suresh", "Usha", "Vinod", "Anita", "Sunil", "Aarti"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Kumar", "Singh", "Patel", "Reddy", "Rao", "Nair", "Joshi",
    "Mehta", "Shah", "Agarwal", "Bhat", "Chawla", "Deshmukh", "Kulkarni", "Iyer", "Iyengar", "Chaudhary",
    "Mishra", "Pandey", "Tripathi", "Srivastava", "Saxena", "Tiwari", "Dube", "Jha", "Thakur", "Rathore",
    "Malhotra", "Kapoor", "Khanna", "Sethi", "Bhasin", "Arora", "Grover", "Taneja", "Bansal", "Goel",
    "Singhal", "Garg", "Jain", "Maheshwari", "Khandelwal", "Mittal", "Somani", "Rathi", "Bihani", "Pareek"
]

BRANCHES = [
    {
        "name": "Computer Science & Engineering (CSE)",
        "courses": ["CS301: Data Structures & Algorithms", "CS302: Operating Systems", "CS303: Database Management Systems", "CS304: Computer Networks", "CS305: Software Engineering", "MA201: Discrete Mathematics"]
    },
    {
        "name": "Artificial Intelligence & Data Science (AI&DS)",
        "courses": ["AI301: Machine Learning Fundamentals", "AI302: Neural Networks & Deep Learning", "DS301: Big Data Analytics", "DS302: Python Data Science Toolkit", "CS303: Database Management Systems", "MA202: Applied Probability & Statistics"]
    },
    {
        "name": "Electronics & Communication Engineering (ECE)",
        "courses": ["EC301: Digital Signal Processing", "EC302: Microprocessors & Microcontrollers", "EC303: Analog Communication Systems", "EC304: VLSI Design", "EC305: Electromagnetic Theory", "MA201: Applied Mathematics"]
    },
    {
        "name": "Electrical & Electronics Engineering (EEE)",
        "courses": ["EE301: Power Systems & Smart Grids", "EE302: Control Systems", "EE303: Electrical Machines II", "EE304: Power Electronics", "EE305: Renewable Energy Systems", "MA201: Applied Mathematics"]
    },
    {
        "name": "Mechanical Engineering (ME)",
        "courses": ["ME301: Thermodynamics & Heat Transfer", "ME302: Fluid Mechanics & Hydraulics", "ME303: CAD/CAM & Robotics", "ME304: Kinematics of Machinery", "ME305: Manufacturing Technology", "MA201: Applied Mathematics"]
    },
    {
        "name": "Civil Engineering (CE)",
        "courses": ["CE301: Structural Analysis", "CE302: Geotechnical Engineering", "CE303: Transportation Engineering", "CE304: Environmental Engineering", "CE305: Concrete Technology", "MA201: Applied Mathematics"]
    },
    {
        "name": "Management (MBA)",
        "courses": ["MG401: Financial Management", "MG402: Marketing Strategy & Digital Media", "MG403: Human Resource Analytics", "MG404: Supply Chain & Logistics", "MG405: Strategic Decision Making", "MG406: Corporate Governance"]
    },
    {
        "name": "Law (BA LLB)",
        "courses": ["LW201: Constitutional Law II", "LW202: Corporate & Commercial Law", "LW203: Criminal Law & Procedure", "LW204: Intellectual Property Rights", "LW205: International Trade Law", "LW206: Environmental Law"]
    }
]

FEE_STATUSES = ["Paid", "Paid", "Paid", "Paid", "Pending ($450.00)", "Pending ($900.00)", "Scholarship Approved (100% Fee Waiver)", "Scholarship Approved (50% Fee Waiver)"]

def generate_100_students():
    random.seed(2026) # Deterministic generation
    students = []
    
    for i in range(1, 101):
        enrollment_no = f"2024IFHE{i:03d}"
        fn = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        ln = LAST_NAMES[(i * 7) % len(LAST_NAMES)]
        name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{i:03d}@ifheindia.edu"
        
        # Mobile number: 10 digits starting with 9, 8, or 7
        prefix = random.choice(["98", "97", "96", "99", "88", "87", "79"])
        suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
        mobile_no = f"+91 {prefix}{suffix}"
        
        branch_obj = BRANCHES[(i - 1) % len(BRANCHES)]
        branch_name = branch_obj["name"]
        
        year = random.choice([1, 2, 3, 4]) if "MBA" not in branch_name and "Law" not in branch_name else random.choice([1, 2])
        sem = (year * 2) - random.choice([0, 1])
        
        # Select 4 to 5 courses
        courses_sample = random.sample(branch_obj["courses"], k=min(5, len(branch_obj["courses"])))
        courses_str = ", ".join(courses_sample)
        
        sgpa = round(random.uniform(6.50, 9.85), 2)
        cgpa = round(max(6.0, sgpa + random.uniform(-0.3, 0.3)), 2)
        if cgpa > 10.0: cgpa = 9.95
        
        attendance = round(random.uniform(72.0, 98.5), 1)
        backlogs = 0 if cgpa > 7.5 else random.choice([0, 0, 1, 2])
        fee_status = random.choice(FEE_STATUSES)
        
        student = {
            "enrollment_no": enrollment_no,
            "name": name,
            "email": email,
            "mobile_no": mobile_no,
            "branch": branch_name,
            "year": year,
            "semester": sem,
            "courses_enrolled": courses_str,
            "sgpa": sgpa,
            "cgpa": cgpa,
            "attendance_pct": attendance,
            "backlogs": backlogs,
            "fee_status": fee_status
        }
        students.append(student)
        
    return students

def seed_database(students):
    db_file = os.path.abspath(DB_PATH)
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        enrollment_no TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        mobile_no TEXT NOT NULL,
        branch TEXT NOT NULL,
        year INTEGER NOT NULL,
        semester INTEGER NOT NULL,
        courses_enrolled TEXT NOT NULL,
        sgpa REAL NOT NULL,
        cgpa REAL NOT NULL,
        attendance_pct REAL NOT NULL,
        backlogs INTEGER NOT NULL,
        fee_status TEXT NOT NULL
    )
    """)
    
    cursor.execute("DELETE FROM students")
    
    for s in students:
        cursor.execute("""
        INSERT INTO students (enrollment_no, name, email, mobile_no, branch, year, semester, courses_enrolled, sgpa, cgpa, attendance_pct, backlogs, fee_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["enrollment_no"], s["name"], s["email"], s["mobile_no"], s["branch"],
            s["year"], s["semester"], s["courses_enrolled"], s["sgpa"], s["cgpa"],
            s["attendance_pct"], s["backlogs"], s["fee_status"]
        ))
        
    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(students)} student records into SQLite database at {db_file}")

def create_raw_txt_file(students):
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
    os.makedirs(raw_dir, exist_ok=True)
    out_file = os.path.join(raw_dir, "ifhe_student_directory_records.txt")
    
    lines = [
        "================================================================================",
        "DEMO DATA — SYNTHETIC STUDENT ACADEMIC & ENROLLMENT DIRECTORY (NOT OFFICIAL)",
        "================================================================================\n",
        "This development-only master document contains synthetic academic, enrollment, and contact records. It must not be treated as official campus data.\n"
    ]
    
    for s in students:
        lines.append(f"STUDENT ENROLLMENT RECORD: {s['enrollment_no']}")
        lines.append(f"• Name: {s['name']}")
        lines.append(f"• Enrollment No: {s['enrollment_no']}")
        lines.append(f"• Email: {s['email']}")
        lines.append(f"• Mobile Number: {s['mobile_no']}")
        lines.append(f"• Branch / Department: {s['branch']}")
        lines.append(f"• Academic Year: Year {s['year']} (Semester {s['semester']})")
        lines.append(f"• Enrolled Courses: {s['courses_enrolled']}")
        lines.append(f"• Current Semester SGPA: {s['sgpa']}")
        lines.append(f"• Cumulative CGPA: {s['cgpa']}")
        lines.append(f"• Attendance Percentage: {s['attendance_pct']}%")
        lines.append(f"• Active Backlogs: {s['backlogs']}")
        lines.append(f"• Tuition Fee Status: {s['fee_status']}")
        lines.append("-" * 60 + "\n")
        
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"Successfully generated RAG document record at {out_file}")

if __name__ == "__main__":
    stus = generate_100_students()
    seed_database(stus)
    create_raw_txt_file(stus)
