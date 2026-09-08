"""
Full Timetable & Scheduling Domain Seeding Script for Chronos Engine.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chronos.introspection.sqlite_introspector import SQLiteIntrospector
from chronos.enrichment.engine import SemanticEnrichmentEngine
from chronos.compiler.compiler import ChronosCompiler
from chronos.runtime.kernel import SimulationKernel
from chronos.materialization.sqlite_writer import SQLiteMaterializer

def seed_timetable_database():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timetable_enterprise.db")
    
    if os.path.exists(db_file):
        os.remove(db_file)

    print("==========================================================================")
    print(" CHRONOS SIMULATION ENGINE: TIMETABLE & SCHEDULING DOMAIN SEEDING")
    print("==========================================================================")

    # 1. Bootstrap Timetable Database Schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE TB_DEPARTMENT (
        dept_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE TB_FACULTY (
        faculty_id TEXT PRIMARY KEY,
        dept_id TEXT REFERENCES TB_DEPARTMENT(dept_id),
        name TEXT NOT NULL
    );

    CREATE TABLE TB_STUDENT (
        student_id TEXT PRIMARY KEY,
        dept_id TEXT REFERENCES TB_DEPARTMENT(dept_id),
        cgpa REAL,
        attendance_pct REAL,
        fee_status TEXT,
        placement_eligible INTEGER
    );

    CREATE TABLE TB_COURSE (
        course_id TEXT PRIMARY KEY,
        course_code TEXT NOT NULL,
        course_name TEXT NOT NULL,
        credits INTEGER,
        dept_id TEXT REFERENCES TB_DEPARTMENT(dept_id)
    );

    CREATE TABLE TB_CLASS_ROOM (
        room_id TEXT PRIMARY KEY,
        room_number TEXT NOT NULL,
        capacity INTEGER
    );

    CREATE TABLE TB_TIME_SLOT (
        slot_id TEXT PRIMARY KEY,
        day_of_week TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL
    );

    CREATE TABLE TB_TIMETABLE_ENTRY (
        schedule_id TEXT PRIMARY KEY,
        course_id TEXT REFERENCES TB_COURSE(course_id),
        faculty_id TEXT REFERENCES TB_FACULTY(faculty_id),
        room_id TEXT REFERENCES TB_CLASS_ROOM(room_id),
        slot_id TEXT REFERENCES TB_TIME_SLOT(slot_id),
        semester TEXT
    );

    CREATE TABLE TB_COURSE_ENROLLMENT (
        enrollment_id TEXT PRIMARY KEY,
        student_id TEXT REFERENCES TB_STUDENT(student_id),
        course_id TEXT REFERENCES TB_COURSE(course_id),
        enrollment_date TEXT
    );

    CREATE TABLE TB_ATTENDANCE (
        attendance_id TEXT PRIMARY KEY,
        student_id TEXT REFERENCES TB_STUDENT(student_id),
        schedule_id TEXT REFERENCES TB_TIMETABLE_ENTRY(schedule_id),
        timestamp TEXT,
        is_present INTEGER
    );

    CREATE TABLE TB_EXAM_RESULT (
        result_id TEXT PRIMARY KEY,
        student_id TEXT REFERENCES TB_STUDENT(student_id),
        score REAL
    );
    """)
    conn.commit()
    print(f"[Phase 1] Created Timetable Database Schema at: {db_file}")

    # 2. Introspect Schema
    print("[Phase 2] Introspecting Timetable Schema via SQLite Connection...")
    introspector = SQLiteIntrospector(domain_name="Timetable_Domain")
    sdm = introspector.inspect(conn)
    print(f"  - Extracted {len(sdm.tables)} tables into Structural Domain Model.")

    # 3. Enrich & Compile
    print("[Phase 3] Compiling Chronos IR Execution Plan...")
    enricher = SemanticEnrichmentEngine()
    bdm = enricher.enrich(sdm)
    compiler = ChronosCompiler(root_seed=2026)
    ir = compiler.compile(bdm)

    # 4. Run Simulation Engine
    print("[Phase 4] Launching Discrete Event Kernel & Seeding Timetable Entries...")
    kernel = SimulationKernel(ir)
    kernel.bootstrap_world({"TB_DEPARTMENT": 1, "TB_FACULTY": 3, "TB_STUDENT": 6})
    events = kernel.run_simulation(ticks=30)
    print(f"  - Simulation Completed ({len(events)} attendance events generated).")

    # 5. Populate SQLite Database
    print("\n[Phase 5] Materializing Timetable datasets directly into SQLite database...")
    SQLiteMaterializer().materialize(kernel.state_store.get_all(), events, conn)

    # 6. Execute SQL Queries to Inspect Generated Timetable
    print("\n==========================================================================")
    print(" 1. GENERATED TIMETABLE SCHEDULE ENTRIES (TB_TIMETABLE_ENTRY)")
    print("==========================================================================")
    cursor.execute("""
    SELECT t.schedule_id, c.course_code, c.course_name, f.name AS faculty, r.room_number, s.day_of_week, s.start_time
    FROM TB_TIMETABLE_ENTRY t
    JOIN TB_COURSE c ON t.course_id = c.course_id
    JOIN TB_FACULTY f ON t.faculty_id = f.faculty_id
    JOIN TB_CLASS_ROOM r ON t.room_id = r.room_id
    JOIN TB_TIME_SLOT s ON t.slot_id = s.slot_id;
    """)
    rows = cursor.fetchall()
    print(f"{'Schedule ID':<22} | {'Code':<7} | {'Course Name':<30} | {'Faculty':<15} | {'Room':<8} | {'Slot'}")
    print("-" * 105)
    for r in rows:
        print(f"{r[0]:<22} | {r[1]:<7} | {r[2]:<30} | {r[3]:<15} | {r[4]:<8} | {r[5]} {r[6]}")

    print("\n==========================================================================")
    print(" 2. COURSE ENROLLMENTS (TB_COURSE_ENROLLMENT)")
    print("==========================================================================")
    cursor.execute("""
    SELECT e.enrollment_id, e.student_id, c.course_code, c.course_name
    FROM TB_COURSE_ENROLLMENT e
    JOIN TB_COURSE c ON e.course_id = c.course_id
    LIMIT 10;
    """)
    rows = cursor.fetchall()
    print(f"{'Enrollment ID':<25} | {'Student ID':<15} | {'Code':<7} | {'Course Name'}")
    print("-" * 75)
    for r in rows:
        print(f"{r[0]:<25} | {r[1]:<15} | {r[2]:<7} | {r[3]}")

    print("\n==========================================================================")
    print(" 3. TIMETABLE-LINKED ATTENDANCE LOGS (TB_ATTENDANCE)")
    print("==========================================================================")
    cursor.execute("""
    SELECT a.attendance_id, a.student_id, a.schedule_id, a.timestamp, a.is_present
    FROM TB_ATTENDANCE a
    LIMIT 10;
    """)
    rows = cursor.fetchall()
    print(f"{'Attendance ID':<22} | {'Student ID':<15} | {'Schedule ID':<22} | {'Timestamp':<19} | {'Status'}")
    print("-" * 95)
    for r in rows:
        print(f"{r[0]:<22} | {r[1]:<15} | {r[2]:<22} | {r[3]:<19} | {'PRESENT' if r[4] == 1 else 'ABSENT'}")
    print("==========================================================================")

    conn.close()

if __name__ == "__main__":
    seed_timetable_database()
