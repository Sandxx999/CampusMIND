"""
Canonical Database Seed Script for CampusMIND 2.0.
Seeds roles, departments, programs, courses, demo users, and student profiles
into the canonical relational schema (SQLite or PostgreSQL).
"""
import os
import sys
import uuid
import random
from datetime import datetime, timezone

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import settings
from db.session import get_db_session, create_tables
from db.models import (
    Role,
    User,
    Department,
    Program,
    Course,
    StudentProfile,
    FacultyProfile,
    AdminProfile,
    Enrollment,
)

from scripts.generate_students import generate_100_students, BRANCHES


def seed_canonical_data():
    """Seeds canonical roles, departments, programs, demo users, and student profiles."""
    logger_msg = f"Seeding canonical relational database at: {settings.DATABASE_URL}"
    print(logger_msg)

    # 1. Ensure tables exist
    create_tables()

    with get_db_session() as session:
        # Check if roles exist
        existing_role = session.get(Role, "role_student")
        if not existing_role:
            roles = [
                Role(id="role_student", name="student", description="Student identity role"),
                Role(id="role_faculty", name="faculty", description="Faculty member role"),
                Role(id="role_admin", name="admin", description="Administrator role"),
            ]
            session.add_all(roles)
            session.flush()

        # Departments
        depts_map = {}
        for b in BRANCHES:
            code = b["name"].split("(")[-1].rstrip(")")
            dept = session.query(Department).filter(Department.code == code).first()
            if not dept:
                dept = Department(
                    id=f"dept_{code.lower()}",
                    code=code,
                    name=b["name"],
                )
                session.add(dept)
                session.flush()
            depts_map[code] = dept

        # Programs
        programs_map = {}
        for code, dept in depts_map.items():
            prog_code = f"PROG_{code}"
            prog = session.query(Program).filter(Program.code == prog_code).first()
            if not prog:
                prog = Program(
                    id=f"prog_{code.lower()}",
                    code=prog_code,
                    name=f"Degree Program in {dept.name}",
                    department_id=dept.id,
                    duration_years=2 if "MBA" in code or "LAW" in code else 4,
                )
                session.add(prog)
                session.flush()
            programs_map[code] = prog

        # Courses
        courses_map = {}
        for b in BRANCHES:
            code = b["name"].split("(")[-1].rstrip(")")
            dept = depts_map[code]
            for c_str in b["courses"]:
                c_code = c_str.split(":")[0].strip()
                c_title = c_str.split(":")[-1].strip()
                course = session.query(Course).filter(Course.code == c_code).first()
                if not course:
                    course = Course(
                        id=f"crs_{c_code.lower()}",
                        code=c_code,
                        title=c_title,
                        department_id=dept.id,
                        credits=3,
                    )
                    session.add(course)
                    session.flush()
                courses_map[c_code] = course

        # Demo Faculty & Admin Users
        admin_user = session.query(User).filter(User.username == "admin1").first()
        if not admin_user:
            admin_user = User(
                id="usr_admin1",
                username="admin1",
                email="admin1@ifheindia.edu",
                display_name="Administrator One",
                status="active",
                role_id="role_admin",
            )
            session.add(admin_user)
            session.flush()

            admin_prof = AdminProfile(
                id="prof_admin1",
                user_id=admin_user.id,
                employee_id="EMP_ADM_001",
                designation="Chief System Administrator",
            )
            session.add(admin_prof)

        faculty_user = session.query(User).filter(User.username == "faculty1").first()
        if not faculty_user:
            faculty_user = User(
                id="usr_faculty1",
                username="faculty1",
                email="faculty1@ifheindia.edu",
                display_name="Dr. Faculty Member",
                status="active",
                role_id="role_faculty",
            )
            session.add(faculty_user)
            session.flush()

            faculty_prof = FacultyProfile(
                id="prof_faculty1",
                user_id=faculty_user.id,
                employee_id="EMP_FAC_001",
                department_id=depts_map["CSE"].id,
                designation="Associate Professor",
            )
            session.add(faculty_prof)

        # 100 Generated Students & Profiles
        students_data = generate_100_students()
        for idx, s in enumerate(students_data, start=1):
            username = "student1" if idx == 1 else f"student_{s['enrollment_no'].lower()}"
            user = session.query(User).filter(User.username == username).first()
            if not user:
                user = User(
                    id=f"usr_std_{idx:03d}",
                    username=username,
                    email=s["email"],
                    display_name=s["name"],
                    status="active",
                    role_id="role_student",
                )
                session.add(user)
                session.flush()

            sp = session.query(StudentProfile).filter(StudentProfile.enrollment_no == s["enrollment_no"]).first()
            if not sp:
                branch_code = s["branch"].split("(")[-1].rstrip(")")
                dept = depts_map.get(branch_code)
                prog = programs_map.get(branch_code)

                sp = StudentProfile(
                    id=f"prof_std_{idx:03d}",
                    user_id=user.id,
                    enrollment_no=s["enrollment_no"],
                    department_id=dept.id if dept else None,
                    program_id=prog.id if prog else None,
                    branch=s["branch"],
                    year=s["year"],
                    semester=s["semester"],
                    courses_enrolled=s["courses_enrolled"],
                    sgpa=s["sgpa"],
                    cgpa=s["cgpa"],
                    attendance_pct=s["attendance_pct"],
                    backlogs=s["backlogs"],
                    fee_status=s["fee_status"],
                    mobile_no=s["mobile_no"],
                )
                session.add(sp)
                session.flush()

                # Enrollments junction entries
                for c_str in s["courses_enrolled"].split(", "):
                    c_code = c_str.split(":")[0].strip()
                    c_obj = courses_map.get(c_code)
                    if c_obj:
                        enr = Enrollment(
                            id=f"enr_{sp.id}_{c_obj.id}",
                            student_profile_id=sp.id,
                            course_id=c_obj.id,
                            academic_year="2024-2025",
                            semester=s["semester"],
                        )
                        session.add(enr)

    print("Canonical database successfully seeded!")


if __name__ == "__main__":
    seed_canonical_data()
