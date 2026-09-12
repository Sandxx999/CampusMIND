"""
Canonical Database Seed Script for CampusMIND 2.0.
Seeds roles, departments, programs, courses, demo users, student profiles,
academic terms, course offerings, attendance, assessments, announcements, campus events,
and knowledge document metadata into the canonical relational schema (SQLite or PostgreSQL).
"""
import os
import sys
import uuid
import random
from datetime import datetime, timezone, timedelta

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
    AcademicTerm,
    CourseOffering,
    AttendanceRecord,
    Assessment,
    AssessmentGrade,
    Announcement,
    CampusEvent,
    EventRegistration,
    KnowledgeDocument,
)

from scripts.generate_students import generate_100_students, BRANCHES


def seed_canonical_data():
    """Seeds canonical roles, departments, programs, demo users, student profiles, and Phase 3 institutional data."""
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
        else:
            faculty_prof = faculty_user.faculty_profile

        # Academic Term
        current_term = session.query(AcademicTerm).filter(AcademicTerm.code == "2024-FALL").first()
        if not current_term:
            current_term = AcademicTerm(
                id="term_2024_fall",
                code="2024-FALL",
                name="Fall 2024 Semester",
                academic_year="2024-2025",
                semester=1,
                is_current=True,
            )
            session.add(current_term)
            session.flush()

        # Course Offerings for Current Term
        offerings_map = {}
        for c_code, course in courses_map.items():
            offering = session.query(CourseOffering).filter(
                CourseOffering.course_id == course.id,
                CourseOffering.term_id == current_term.id,
                CourseOffering.section == "A"
            ).first()
            if not offering:
                offering = CourseOffering(
                    id=f"offering_{course.code.lower()}_fall24",
                    course_id=course.id,
                    term_id=current_term.id,
                    faculty_profile_id=faculty_prof.id if faculty_prof else None,
                    section="A",
                    room="Room 302, Academic Block",
                    schedule="Mon/Wed 10:00 - 11:30 AM",
                    max_capacity=60,
                    status="active",
                )
                session.add(offering)
                session.flush()
            offerings_map[c_code] = offering

        # 100 Generated Students & Profiles
        students_data = generate_100_students()
        student_profiles_list = []
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
                    offering_obj = offerings_map.get(c_code)
                    if c_obj:
                        enr = Enrollment(
                            id=f"enr_{sp.id}_{c_obj.id}",
                            student_profile_id=sp.id,
                            course_id=c_obj.id,
                            course_offering_id=offering_obj.id if offering_obj else None,
                            academic_year="2024-2025",
                            semester=s["semester"],
                        )
                        session.add(enr)
            student_profiles_list.append(sp)

        # Seed Sample Attendance Records for student1 & first 5 students
        std1_sp = student_profiles_list[0] if student_profiles_list else None
        if std1_sp:
            att_exists = session.query(AttendanceRecord).filter(AttendanceRecord.student_profile_id == std1_sp.id).first()
            if not att_exists:
                now_dt = datetime.now(timezone.utc)
                for i in range(10):
                    day_dt = now_dt - timedelta(days=i)
                    for c_code, offering in list(offerings_map.items())[:3]:
                        status_val = "present" if i % 4 != 0 else "absent"
                        att_rec = AttendanceRecord(
                            id=f"att_{std1_sp.id}_{offering.id}_{i}",
                            student_profile_id=std1_sp.id,
                            course_offering_id=offering.id,
                            course_id=offering.course_id,
                            date=day_dt,
                            status=status_val,
                            recorded_by_id=faculty_user.id if faculty_user else None,
                            remarks="Regular Class Session",
                        )
                        session.add(att_rec)

        # Seed Sample Assessments & Grades
        asm_exists = session.query(Assessment).first()
        if not asm_exists:
            sample_offering = list(offerings_map.values())[0] if offerings_map else None
            if sample_offering:
                midterm = Assessment(
                    id="asm_midterm_cs101",
                    title="Midterm Examination",
                    assessment_type="midterm",
                    max_marks=100.0,
                    weightage=30.0,
                    course_offering_id=sample_offering.id,
                    course_id=sample_offering.course_id,
                    created_by_id=faculty_user.id if faculty_user else admin_user.id,
                    status="published",
                )
                quiz1 = Assessment(
                    id="asm_quiz1_cs101",
                    title="Quiz 1: Core Fundamentals",
                    assessment_type="quiz",
                    max_marks=20.0,
                    weightage=10.0,
                    course_offering_id=sample_offering.id,
                    course_id=sample_offering.course_id,
                    created_by_id=faculty_user.id if faculty_user else admin_user.id,
                    status="published",
                )
                session.add_all([midterm, quiz1])
                session.flush()

                if std1_sp:
                    grd1 = AssessmentGrade(
                        id=f"grd_{midterm.id}_{std1_sp.id}",
                        assessment_id=midterm.id,
                        student_profile_id=std1_sp.id,
                        obtained_marks=88.5,
                        grade="A",
                        feedback="Excellent problem analysis.",
                        evaluator_id=faculty_user.id if faculty_user else None,
                    )
                    grd2 = AssessmentGrade(
                        id=f"grd_{quiz1.id}_{std1_sp.id}",
                        assessment_id=quiz1.id,
                        student_profile_id=std1_sp.id,
                        obtained_marks=18.0,
                        grade="A+",
                        feedback="Top score in quiz.",
                        evaluator_id=faculty_user.id if faculty_user else None,
                    )
                    session.add_all([grd1, grd2])

        # Seed Sample Institutional Announcements
        ann_exists = session.query(Announcement).first()
        if not ann_exists:
            ann1 = Announcement(
                id="ann_001",
                title="Fall 2024 Midterm Examination Schedule Released",
                content="The official timetable for Fall 2024 Midterm Examinations is now published. Please inspect the portal for hall ticket downloads.",
                author_id=admin_user.id if admin_user else faculty_user.id,
                audience="all",
                status="published",
                priority="high",
            )
            ann2 = Announcement(
                id="ann_002",
                title="Campus AI & Machine Learning Research Workshop",
                content="Department of Computer Science & Engineering is hosting a 2-day hands-on workshop on generative AI systems.",
                author_id=faculty_user.id if faculty_user else admin_user.id,
                audience="students",
                department_id=depts_map["CSE"].id if "CSE" in depts_map else None,
                status="published",
                priority="normal",
            )
            session.add_all([ann1, ann2])

        # Seed Sample Campus Events
        evt_exists = session.query(CampusEvent).first()
        if not evt_exists:
            evt1 = CampusEvent(
                id="evt_001",
                title="Campus Technology & Innovation Summit 2025",
                description="Annual flagship technology gathering featuring keynote talks, project demonstrations, and industry panel sessions.",
                location="Main Auditorium, Block A",
                start_time=datetime.now(timezone.utc) + timedelta(days=7),
                end_time=datetime.now(timezone.utc) + timedelta(days=7, hours=6),
                organizer_id=admin_user.id if admin_user else faculty_user.id,
                audience="all",
                category="seminar",
                capacity=300,
                requires_registration=True,
                status="scheduled",
            )
            session.add(evt1)

        # Seed Sample Knowledge Documents
        doc_exists = session.query(KnowledgeDocument).first()
        if not doc_exists:
            doc1 = KnowledgeDocument(
                id="doc_001",
                title="Institutional Academic Regulations & Evaluation Framework",
                file_path="data/academic_rules.txt",
                category="policy",
                audience="all",
                version="2024.1",
                is_active=True,
                chunk_count=12,
                uploader_id=admin_user.id if admin_user else None,
            )
            doc2 = KnowledgeDocument(
                id="doc_002",
                title="Student Code of Conduct & Honor Code",
                file_path="data/student_handbook.txt",
                category="handbook",
                audience="students",
                version="2024.2",
                is_active=True,
                chunk_count=8,
                uploader_id=admin_user.id if admin_user else None,
            )
            session.add_all([doc1, doc2])

    print("Canonical database with Phase 3 institutional domain successfully seeded!")


if __name__ == "__main__":
    seed_canonical_data()
