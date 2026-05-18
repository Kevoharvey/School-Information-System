# Galala SIS — Developer Documentation
### Database Schema & Application Query Reference

> **Version:** 1.0 | **Stack:** Flask · MySQL 8 · Flask-Bcrypt · Google Gemini  
> **File:** `app.py` + `db.sql` + `db_config.py`

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Database Schema](#2-database-schema)
   - 2.1 [Core Auth Tables](#21-core-auth-tables)
   - 2.2 [People Tables](#22-people-tables)
   - 2.3 [Academic Structure Tables](#23-academic-structure-tables)
   - 2.4 [Activity & Communication Tables](#24-activity--communication-tables)
   - 2.5 [Registration Tables](#25-registration-tables)
   - 2.6 [Archive & Logging Tables](#26-archive--logging-tables)
   - 2.7 [Views](#27-views)
   - 2.8 [Entity-Relationship Summary](#28-entity-relationship-summary)
3. [Application Query Reference](#3-application-query-reference)
   - 3.1 [Authentication & Session](#31-authentication--session)
   - 3.2 [Dashboard](#32-dashboard)
   - 3.3 [Students](#33-students)
   - 3.4 [Student Profile](#34-student-profile)
   - 3.5 [Teachers & Academic Management](#35-teachers--academic-management)
   - 3.6 [Assignments](#36-assignments)
   - 3.7 [Gradebook](#37-gradebook)
   - 3.8 [Attendance](#38-attendance)
   - 3.9 [Schedule](#39-schedule)
   - 3.10 [Enrollment Management](#310-enrollment-management)
   - 3.11 [Analytics](#311-analytics)
   - 3.12 [Notifications](#312-notifications)
   - 3.13 [Classrooms](#313-classrooms)
   - 3.14 [Departments](#314-departments)
   - 3.15 [Registration Review (Admin)](#315-registration-review-admin)
   - 3.16 [AI Assistant](#316-ai-assistant)
   - 3.17 [Activity Logs](#317-activity-logs)
4. [Access Control & Decorators](#4-access-control--decorators)
5. [Helper Functions Reference](#5-helper-functions-reference)
6. [Key SQL Patterns](#6-key-sql-patterns)

---

## 1. Architecture Overview

Galala SIS is a multi-role school information system with three user roles:

| Role | Access Level | Key Capabilities |
|------|-------------|-----------------|
| `admin` | Full system access | All CRUD, registrations, classrooms, AI assistant |
| `teacher` | Academic operations | Own students, assignments, attendance, gradebook |
| `student` | Read-only personal data | Own profile, grades, assignments, schedule |

**Database connection** is handled by `db_config.py` which exposes two helpers used everywhere in `app.py`:

- `query(sql, params, fetchone)` — runs `SELECT` statements, returns list of dicts (or one dict if `fetchone=True`)
- `execute(sql, params)` — runs `INSERT/UPDATE/DELETE`, returns `lastrowid`

---

## 2. Database Schema

### 2.1 Core Auth Tables

#### `Users`
The single authentication table for all human actors in the system.

| Column | Type | Notes |
|--------|------|-------|
| `User_ID` | INT PK AUTO_INCREMENT | Primary identifier |
| `Full_Name` | VARCHAR(100) NOT NULL | Display name |
| `Email` | VARCHAR(150) NOT NULL UNIQUE | Login email (case-insensitive matching enforced in app) |
| `Password_Hash` | VARCHAR(255) NOT NULL | bcrypt hash (legacy scrypt hashes auto-upgraded on login) |
| `Role` | ENUM('student','teacher','admin') | Determines UI and access level |
| `Created_At` | TIMESTAMP | Auto-set on creation |

**Seeded admin account:** `Admin@gmail.com` (scrypt hash — upgraded to bcrypt on first login).

**Design notes:**
- `Email` is always stored and matched with `LOWER()` to prevent case-sensitivity issues.
- Password hashing uses `flask-bcrypt`. A legacy scrypt-to-bcrypt migration runs transparently on successful login via `verify_password_and_upgrade_if_needed()`.

---

### 2.2 People Tables

#### `Parents`
Extracted from `Student` as a separate normalized table. Multiple students can share one parent record.

| Column | Type | Notes |
|--------|------|-------|
| `Parent_ID` | INT PK AUTO_INCREMENT | |
| `Parent_Name` | VARCHAR(100) NOT NULL | |
| `Parent_Email` | VARCHAR(150) | Used for parent follow-up and expulsion emails |
| `Parent_Phone` | VARCHAR(20) | |

**App helper:** `ensure_parent(name, phone, email)` — inserts a new parent only if no matching `(Parent_Name, Parent_Email)` pair exists. Returns `Parent_ID`.

---

#### `Student`
The core student record, linked to `Users` for authentication and `Parents` for guardian data.

| Column | Type | Notes |
|--------|------|-------|
| `Student_ID` | INT PK AUTO_INCREMENT | |
| `User_ID` | INT UNIQUE FK → Users | One-to-one; cascades delete |
| `Parent_ID` | INT FK → Parents | SET NULL on parent delete |
| `Fname` / `Lname` | VARCHAR(50) NOT NULL | |
| `Birth_Date` | DATE | |
| `Gender` | VARCHAR(20) | |
| `Nationality` | VARCHAR(80) | |
| `Level` | VARCHAR(50) | Grade level, e.g. "Grade 10", "KG 1" |
| `Student_Email` | VARCHAR(150) | Personal email (different from login email) |
| `Student_Phone` | VARCHAR(20) | |
| `Student_Address` | VARCHAR(250) | |
| `Previous_School` | VARCHAR(150) | |
| `Student_Photo` | VARCHAR(255) | File path under `static/uploads/` |
| `Birth_Certificate` | VARCHAR(255) | File path |
| `Previous_Transcript` | VARCHAR(255) | File path |
| `Status` | ENUM('Active','Enrolled','Pending') | Default `Pending` |
| `Enrolled_At` | TIMESTAMP | Auto-set |

**Cascade behavior:** Deleting a `Users` row cascades to `Student`, which in turn cascades to `Enrollments`, `Submission`, and `Attendance`.

---

#### `Employee`
All non-student staff. Currently only `instructor` type has downstream records in `Instructor`.

| Column | Type | Notes |
|--------|------|-------|
| `Emp_ID` | INT PK AUTO_INCREMENT | |
| `User_ID` | INT UNIQUE FK → Users | Cascades delete |
| `Dept_ID` | INT NOT NULL FK → Department | RESTRICT on delete (can't delete dept with staff) |
| `Emp_FName` / `Emp_LName` | VARCHAR(50) NOT NULL | |
| `Emp_Email` | VARCHAR(150) | |
| `Emp_Phone` | VARCHAR(20) | |
| `Employment_Date` | DATE | |
| `Emp_Type` | ENUM('instructor','admin_staff','support') | Default `instructor` |
| `Is_Supervisor` | BOOLEAN | Default FALSE |

---

#### `Instructor`
A subtype table — every teacher who can teach subjects must have an `Instructor` row. This is a pure FK-based subtype (no extra columns).

| Column | Type | Notes |
|--------|------|-------|
| `Emp_ID` | INT PK FK → Employee | Cascades delete |

**Why a separate table?** Keeps the schema extensible — admin staff or support staff in `Employee` who are not instructors simply have no row here.

---

### 2.3 Academic Structure Tables

#### `Department`
Academic departments. Has a self-referencing FK to `Employee` for the department head.

| Column | Type | Notes |
|--------|------|-------|
| `Dept_ID` | INT PK AUTO_INCREMENT | |
| `Dept_Name` | VARCHAR(100) NOT NULL UNIQUE | |
| `Dept_Head_ID` | INT FK → Employee | SET NULL on employee delete; added via `ALTER TABLE` after `Employee` is created |

**Circular FK resolution:** `Department` is created before `Employee`, so `Dept_Head_ID`'s FK constraint is added with `ALTER TABLE` after `Employee` exists.

---

#### `Subject`
A course or class that can be assigned to teachers and enrolled in by students.

| Column | Type | Notes |
|--------|------|-------|
| `Subject_ID` | INT PK AUTO_INCREMENT | |
| `Subject_Name` | VARCHAR(100) NOT NULL | |
| `Subject_Level` | VARCHAR(50) | Grade level filter, e.g. "Grade 9" |
| `Subject_Slots` | INT | Number of scheduled periods per week |
| `Dept_ID` | INT FK → Department | SET NULL on dept delete |

**Note:** Classroom is NOT on `Subject` — it belongs to `Schedule_Entry` because the same subject can use different rooms on different days.

---

#### `Teaches`
Many-to-many junction between `Instructor` and `Subject`.

| Column | Type | Notes |
|--------|------|-------|
| `Emp_ID` | INT PK (composite) FK → Instructor | Cascades delete |
| `Subject_ID` | INT PK (composite) FK → Subject | Cascades delete |

**App behavior:** `INSERT IGNORE INTO Teaches` is used throughout to avoid duplicate errors when syncing from schedule entries.

---

#### `Enrollments`
Records which students are taking which subjects in which semester. Stores the final grade here (not in `Submission`).

| Column | Type | Notes |
|--------|------|-------|
| `Enrollment_ID` | INT PK AUTO_INCREMENT | |
| `Student_ID` | INT NOT NULL FK → Student | Cascades delete |
| `Subject_ID` | INT NOT NULL FK → Subject | Cascades delete |
| `Semester` | VARCHAR(20) | Default `'CURRENT'`; values like `SEM1`, `SEM2`, `SUMMER` |
| `Academic_Year` | VARCHAR(20) | e.g. `"2026/2027"` |
| `Final_Grade` | DECIMAL(5,2) | Set by teacher via Gradebook |
| `Status` | ENUM('Active','Completed','Dropped','Failed') | Default `Active` |
| `Enrolled_At` | TIMESTAMP | Auto-set |

**Unique constraint:** `(Student_ID, Subject_ID, Semester)` — a student can only be enrolled once per subject per semester.

---

#### `Classroom`
Physical rooms used in the schedule.

| Column | Type | Notes |
|--------|------|-------|
| `Classroom_ID` | INT PK AUTO_INCREMENT | |
| `Classroom_Name` | VARCHAR(50) NOT NULL UNIQUE | |
| `Capacity` | INT | |
| `Building` | VARCHAR(50) | |
| `Floor` | VARCHAR(20) | |

---

#### `Schedule_Entry`
A specific time slot where a subject is taught in a room by an instructor.

| Column | Type | Notes |
|--------|------|-------|
| `Entry_ID` | INT PK AUTO_INCREMENT | |
| `Subject_ID` | INT NOT NULL FK → Subject | Cascades delete |
| `Classroom_ID` | INT FK → Classroom | SET NULL on room delete |
| `Emp_ID` | INT FK → Instructor | SET NULL on teacher delete |
| `Semester` | VARCHAR(20) | |
| `Academic_Year` | VARCHAR(20) | |
| `Day_Of_Week` | ENUM('Monday'…'Sunday') | |
| `Start_Time` | TIME | |
| `End_Time` | TIME | |

**Double-booking prevention via UNIQUE constraints:**
- `uq_classroom_booking (Classroom_ID, Day_Of_Week, Start_Time, Semester, Academic_Year)` — same room can't have two classes at once.
- `uq_instructor_booking (Emp_ID, Day_Of_Week, Start_Time, Semester, Academic_Year)` — same teacher can't teach two classes at once.

The app checks for `None` return from `execute()` to detect the constraint violation and shows a flash error.

---

#### `Assignment`
An assignment created by a teacher for a subject.

| Column | Type | Notes |
|--------|------|-------|
| `Assignment_ID` | INT PK AUTO_INCREMENT | |
| `Title` | VARCHAR(200) NOT NULL | |
| `Description` | TEXT | |
| `Subject_ID` | INT NOT NULL FK → Subject | Cascades delete |
| `Emp_ID` | INT FK → Instructor | SET NULL on teacher delete |
| `Due_Date` | DATE | |
| `Max_Score` | DECIMAL(5,2) | Default 100 |
| `File_Path` | VARCHAR(255) | Optional attached file |
| `Status` | ENUM('Active','Grading','Published','Closed') | Default `Active` |
| `Created_At` | TIMESTAMP | Auto-set |

---

#### `Submission`
A student's response to an assignment. Scored and given feedback by the teacher.

| Column | Type | Notes |
|--------|------|-------|
| `Sub_ID` | INT PK AUTO_INCREMENT | |
| `Assignment_ID` | INT NOT NULL FK → Assignment | Cascades delete |
| `Student_ID` | INT NOT NULL FK → Student | Cascades delete |
| `Submitted_At` | TIMESTAMP | Auto-set |
| `File_Path` | VARCHAR(255) | Student's uploaded solution |
| `Score` | DECIMAL(5,2) | Filled by teacher |
| `Feedback` | TEXT | Filled by teacher |

**Unique constraint:** `(Assignment_ID, Student_ID)` — one submission per student per assignment.

---

#### `Attendance`
Records per-session presence for a student, linked to a specific `Schedule_Entry` (not just a subject).

| Column | Type | Notes |
|--------|------|-------|
| `Att_ID` | INT PK AUTO_INCREMENT | |
| `Student_ID` | INT NOT NULL FK → Student | Cascades delete |
| `Entry_ID` | INT NOT NULL FK → Schedule_Entry | Cascades delete |
| `Att_Date` | DATE NOT NULL | |
| `Present` | BOOLEAN | Default TRUE |

**Unique constraint:** `(Student_ID, Entry_ID, Att_Date)` — prevents duplicate records for the same session. The save route uses an upsert pattern (check-then-update-or-insert).

---

### 2.4 Activity & Communication Tables

#### `Notification`
In-app notifications. `User_ID = NULL` means broadcast to everyone.

| Column | Type | Notes |
|--------|------|-------|
| `Notif_ID` | INT PK AUTO_INCREMENT | |
| `User_ID` | INT FK → Users | NULL = broadcast; cascades delete |
| `Title` | VARCHAR(200) NOT NULL | |
| `Message` | TEXT | |
| `Type` | ENUM('assignment','grade','announcement','system','attendance') | Default `announcement` |
| `Is_Read` | BOOLEAN | Default FALSE |
| `Created_At` | TIMESTAMP | Auto-set |

---

#### `Activity_Logs`
Audit trail for all significant actions in the app.

| Column | Type | Notes |
|--------|------|-------|
| `Log_ID` | INT PK AUTO_INCREMENT | |
| `User_ID` | INT FK → Users | SET NULL if user deleted |
| `Action` | VARCHAR(100) NOT NULL | Human-readable description |
| `Table_Name` | VARCHAR(100) | Which entity was affected |
| `Action_Time` | TIMESTAMP | Auto-set |

**App helper:** `log_activity(action, table_name)` — reads `session["user_id"]` and inserts the log row.

---

### 2.5 Registration Tables

These tables store online applications before approval. They are intentionally separate from the main `Student`/`Employee` tables — approved records are copied over, not moved.

#### `Student_Registration`

| Column | Type | Notes |
|--------|------|-------|
| `Student_Reg_ID` | INT PK AUTO_INCREMENT | |
| `Full_Name` | VARCHAR(100) NOT NULL | |
| `Birth_Date`, `Gender`, `Nationality` | Various | Personal info |
| `Email` | VARCHAR(150) | Applicant/contact email |
| `Phone` | VARCHAR(20) | |
| `Grade_Applied` | VARCHAR(50) | Requested grade level |
| `Parent_Name`, `Parent_Phone`, `Parent_Email` | Various | Guardian info |
| `Address` | VARCHAR(250) | |
| `Previous_School` | VARCHAR(150) | |
| `Birth_Certificate`, `Student_Photo`, `Previous_Transcript` | VARCHAR(255) | Uploaded file paths |
| `Status` | ENUM('Pending','Approved','Rejected') | Default `Pending` |
| `Submitted_At` | TIMESTAMP | Auto-set |

---

#### `Teacher_Registration`

| Column | Type | Notes |
|--------|------|-------|
| `Teacher_Reg_ID` | INT PK AUTO_INCREMENT | |
| `Full_Name` | VARCHAR(100) NOT NULL | |
| `Contact_Email` | VARCHAR(150) NOT NULL | |
| `Phone_Number` | VARCHAR(20) NOT NULL | |
| `Department` | VARCHAR(100) NOT NULL | |
| `Specialization` | VARCHAR(150) | |
| `Qualification` | VARCHAR(200) NOT NULL | |
| `Available_Start_Date` | DATE | |
| `Address` | TEXT | |
| `Status` | ENUM('Pending','Approved','Rejected') | Default `Pending` |
| `Submitted_At` | TIMESTAMP | Auto-set |

---

### 2.6 Archive & Logging Tables

#### `Graduated_Student`
Preserves a record of students who have been graduated and removed from active tables. No FK to `Student` — the original row is deleted.

| Column | Type | Notes |
|--------|------|-------|
| `Grad_ID` | INT PK AUTO_INCREMENT | |
| `Student_ID` | INT | Historical reference only, no FK |
| `Full_Name` | VARCHAR(100) | |
| `Email` | VARCHAR(150) | |
| `Graduation_Date` | DATE | |
| `Level_At_Graduation` | VARCHAR(50) | |

---

### 2.7 Views

Five pre-joined views eliminate repetitive JOIN boilerplate and are used throughout `app.py` instead of raw table joins.

#### `v_student_full`
Joins `Student` + `Parents` + `Users`. Used in student listing, profile, and deletion.

```sql
SELECT
    s.Student_ID, s.User_ID, s.Fname, s.Lname,
    CONCAT(s.Fname,' ',s.Lname) AS Full_Name,
    s.Level, s.Birth_Date, s.Gender, s.Nationality,
    s.Student_Email, s.Student_Phone, s.Student_Address,
    s.Previous_School, s.Student_Photo, s.Status, s.Enrolled_At,
    s.Birth_Certificate, s.Previous_Transcript,
    p.Parent_ID, p.Parent_Name, p.Parent_Email, p.Parent_Phone,
    u.Email AS Login_Email
FROM Student s
LEFT JOIN Parents  p ON s.Parent_ID = p.Parent_ID
LEFT JOIN Users    u ON s.User_ID   = u.User_ID;
```

**Used in:** `students()`, `student_profile()`, `delete_student()`, `follow_up_parent()`, `expel_from_subject()`

---

#### `v_teacher_full`
Joins `Employee` + `Instructor` + `Department` + `Users`. Only instructor-type employees appear.

```sql
SELECT
    e.Emp_ID, e.User_ID, e.Emp_FName, e.Emp_LName,
    CONCAT(e.Emp_FName,' ',e.Emp_LName) AS Full_Name,
    e.Emp_Email, e.Emp_Phone, e.Employment_Date,
    e.Dept_ID, d.Dept_Name, e.Is_Supervisor,
    u.Email AS Login_Email
FROM Employee   e
JOIN Instructor i ON e.Emp_ID  = i.Emp_ID
JOIN Department d ON e.Dept_ID = d.Dept_ID
LEFT JOIN Users u ON e.User_ID = u.User_ID;
```

**Used in:** `teachers()`

---

#### `v_enrollment_detail`
Joins `Enrollments` + `Student` + `Subject` + `Department` + `Teacher`. Ideal for the "My Grades" page and gradebook.

```sql
SELECT
    en.Enrollment_ID, en.Student_ID, en.Subject_ID,
    en.Semester, en.Academic_Year, en.Final_Grade, en.Status AS Enroll_Status,
    CONCAT(s.Fname,' ',s.Lname) AS Student_Name,
    s.Level, s.Student_Email,
    sub.Subject_Name, sub.Subject_Level,
    d.Dept_Name,
    CONCAT(e.Emp_FName,' ',e.Emp_LName) AS Teacher_Name
FROM Enrollments  en
JOIN Student       s   ON en.Student_ID  = s.Student_ID
JOIN Subject       sub ON en.Subject_ID  = sub.Subject_ID
LEFT JOIN Department d  ON sub.Dept_ID   = d.Dept_ID
LEFT JOIN Teaches   t   ON sub.Subject_ID = t.Subject_ID
LEFT JOIN Instructor i  ON t.Emp_ID       = i.Emp_ID
LEFT JOIN Employee  e   ON i.Emp_ID       = e.Emp_ID;
```

**Used in:** `my_subjects()`

---

#### `v_schedule_full`
Joins `Schedule_Entry` + `Subject` + `Classroom` + `Employee`. Aliased time columns (`Start_T`, `End_T`) are normalized in the route with `.setdefault()`.

```sql
SELECT
    se.Entry_ID, se.Day_Of_Week,
    TIME_FORMAT(se.Start_Time,'%H:%i') AS Start_T,
    TIME_FORMAT(se.End_Time,  '%H:%i') AS End_T,
    se.Semester, se.Academic_Year,
    sub.Subject_ID, sub.Subject_Name, sub.Subject_Level,
    c.Classroom_ID, c.Classroom_Name, c.Building, c.Floor,
    e.Emp_ID, CONCAT(e.Emp_FName,' ',e.Emp_LName) AS Teacher_Name
FROM Schedule_Entry se
JOIN Subject        sub ON se.Subject_ID   = sub.Subject_ID
LEFT JOIN Classroom   c ON se.Classroom_ID = c.Classroom_ID
LEFT JOIN Employee    e ON se.Emp_ID       = e.Emp_ID;
```

**Used in:** `schedule()`

---

#### `v_attendance_full`
Resolves `Subject_ID` cheaply through `Schedule_Entry` — avoids joining back to `Subject` in every attendance query.

```sql
SELECT
    a.Att_ID, a.Student_ID, a.Entry_ID, a.Att_Date, a.Present,
    se.Subject_ID, se.Day_Of_Week,
    sub.Subject_Name,
    CONCAT(s.Fname,' ',s.Lname) AS Student_Name
FROM Attendance     a
JOIN Schedule_Entry se  ON a.Entry_ID   = se.Entry_ID
JOIN Subject        sub ON se.Subject_ID = sub.Subject_ID
JOIN Student        s   ON a.Student_ID  = s.Student_ID;
```

**Used in:** `attendance()` (summary section)

---

### 2.8 Entity-Relationship Summary

```
Users ──────────────┬──── Student ────┬──── Enrollments ──── Subject ──── Teaches ──── Instructor
  │                 │         │       │                          │                          │
  │                 │      Parents    └──── Submission           └──── Department           │
  │                 │                                                       │               │
  └── Employee ─────┘                 Assignment ─────────────────────────────────── (Emp_ID FK)
        │
        └── Instructor ──── Teaches ──── Subject
                 │
                 └──── Schedule_Entry ──── Classroom
                              │
                              └──── Attendance

Users ──── Notification
Users ──── Activity_Logs
Student_Registration  (independent, copied on approval)
Teacher_Registration  (independent, copied on approval)
Graduated_Student     (archive, no live FKs)
```

---

## 3. Application Query Reference

### 3.1 Authentication & Session

#### Login
```sql
SELECT * FROM Users WHERE LOWER(Email) = %s
```
Fetches the user by email (case-insensitive). Password is verified in Python using `flask-bcrypt`. If the stored hash is a legacy scrypt format, the app automatically re-hashes and saves the bcrypt version.

**Route:** `POST /login`

---

#### Password Reset
```sql
SELECT User_ID FROM Users WHERE LOWER(Email) = %s

UPDATE Users SET Password_Hash = %s WHERE User_ID = %s
```
Looks up the account, then overwrites the hash. No token or expiry — direct reset by the account holder.

**Route:** `POST /forgot-password`

---

#### Context Processor (Nav Photo)
```sql
SELECT Student_Photo FROM Student WHERE User_ID = %s
```
Runs on every authenticated page render to display the student's photo in the top navigation bar.

**Function:** `inject_user()` (context processor, runs globally)

---

### 3.2 Dashboard

The dashboard queries differ per role. All three branches are documented below.

#### Admin / General Stats
```sql
SELECT COUNT(*) AS c FROM Student
SELECT COUNT(*) AS c FROM Instructor
SELECT COUNT(*) AS c FROM Classroom
SELECT COUNT(DISTINCT Student_ID) AS c FROM Enrollments WHERE Final_Grade >= 90
```
Counts for the four stat cards on the admin/default dashboard. The last query counts students with at least one grade of 90+.

---

#### Admin — Recent Enrollments
```sql
SELECT Student_ID, CONCAT(Fname,' ',Lname) AS name,
       Level AS grade, Status, Enrolled_At
FROM Student
ORDER BY Enrolled_At DESC
LIMIT 6
```

---

#### Teacher Stats
```sql
-- Students taught by this teacher
SELECT COUNT(DISTINCT en.Student_ID) AS c
FROM Enrollments en
JOIN Teaches t ON en.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s

-- Total instructors
SELECT COUNT(*) AS c FROM Instructor

-- Assignments created
SELECT COUNT(*) AS c FROM Assignment WHERE Emp_ID = %s

-- Top students (grade ≥ 90) in teacher's subjects
SELECT COUNT(DISTINCT en.Student_ID) AS c
FROM Enrollments en
JOIN Teaches t ON en.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s AND en.Final_Grade >= 90
```

---

#### Teacher — Recent Student List
```sql
SELECT DISTINCT s.Student_ID, CONCAT(s.Fname,' ',s.Lname) AS name,
       s.Level AS grade, s.Status, s.Enrolled_At
FROM Student s
JOIN Enrollments en ON s.Student_ID = en.Student_ID
JOIN Teaches t ON en.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s
ORDER BY s.Enrolled_At DESC
LIMIT 6
```

---

#### Student Stats
```sql
-- Number of subject enrollments
SELECT COUNT(*) AS c FROM Enrollments WHERE Student_ID = %s

-- Total distinct assignments in school
SELECT COUNT(DISTINCT Assignment_ID) AS c FROM Assignment

-- Assignments available to this student via their enrolled subjects
SELECT COUNT(*) AS c
FROM Assignment a
JOIN Enrollments en ON a.Subject_ID = en.Subject_ID
WHERE en.Student_ID = %s

-- Graded submissions
SELECT COUNT(*) AS c FROM Submission
WHERE Student_ID = %s AND Score IS NOT NULL
```

---

#### Upcoming Assignments (all roles)
```sql
SELECT a.Assignment_ID, a.Title, s.Subject_Name, a.Due_Date, a.Status
FROM Assignment a
JOIN Subject s ON a.Subject_ID = s.Subject_ID
[WHERE a.Emp_ID = %s  -- teacher only]
[JOIN Enrollments en ON a.Subject_ID = en.Subject_ID WHERE en.Student_ID = %s  -- student]
ORDER BY a.Due_Date IS NULL, a.Due_Date ASC
LIMIT 5
```
`ORDER BY a.Due_Date IS NULL` pushes NULL due-dates to the bottom without a `CASE` expression.

---

### 3.3 Students

#### List Students (Admin)
```sql
SELECT sf.Student_ID, sf.Fname, sf.Lname, sf.Level, ...
FROM v_student_full sf
WHERE (%s='' OR sf.Level LIKE %s)
  AND (%s='' OR sf.Status = %s)
  AND (%s='' OR CONCAT(sf.Fname,' ',sf.Lname) LIKE %s
              OR sf.Student_Email LIKE %s
              OR CAST(sf.Student_ID AS CHAR) LIKE %s)
ORDER BY sf.Level, sf.Enrolled_At DESC
```
Empty string parameters act as "no filter" — avoids building dynamic SQL strings. Passing `''` makes the `OR` condition always true for that filter.

---

#### List Students by Subject (Teacher)
```sql
SELECT sf.*
FROM v_student_full sf
JOIN Enrollments en ON sf.Student_ID = en.Student_ID
WHERE en.Subject_ID = %s
  AND (%s='' OR CONCAT(sf.Fname,' ',sf.Lname) LIKE %s ...)
ORDER BY sf.Level, sf.Enrolled_At DESC
```

---

#### Duplicate Email Check
```sql
SELECT User_ID FROM Users WHERE LOWER(Email) = %s
```
Runs before any student or teacher creation to prevent duplicate accounts.

---

#### Add Student
```sql
INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
VALUES (%s, %s, %s, 'student')

INSERT INTO Student
(User_ID, Parent_ID, Fname, Lname, Birth_Date, Gender, Nationality,
 Level, Student_Email, Student_Phone, Student_Address, Previous_School,
 Student_Photo, Birth_Certificate, Previous_Transcript, Status)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
```
Users row created first; its `lastrowid` is used as `User_ID` in the Student insert.

---

#### Edit Student
```sql
UPDATE Student
SET Fname=%s, Lname=%s, Birth_Date=%s, ...,
    Parent_ID=%s, Status=%s
WHERE Student_ID = %s

UPDATE Users SET Full_Name=%s, Email=%s WHERE User_ID = %s
```
Both tables updated in a single request to stay in sync.

---

#### Delete Student
```sql
-- Get full student info for email + cascade
SELECT sf.User_ID, sf.Fname, sf.Lname, sf.Student_Email,
       sf.Parent_Email, sf.Login_Email AS User_Email
FROM v_student_full sf
WHERE sf.Student_ID = %s

-- Cascade delete (Student row deleted via FK cascade from Users)
DELETE FROM Users WHERE User_ID = %s

-- Clean up the source registration record
DELETE FROM Student_Registration
WHERE Full_Name=%s OR Email=%s OR Parent_Email=%s
```
Deleting `Users` triggers FK cascade: `Student → Enrollments`, `Student → Submission`, `Student → Attendance` are all deleted automatically.

---

#### Graduate Student
```sql
INSERT INTO Graduated_Student
(Student_ID, Full_Name, Email, Graduation_Date, Level_At_Graduation)
VALUES (%s,%s,%s,%s,%s)

DELETE FROM Student WHERE Student_ID = %s
DELETE FROM Users WHERE User_ID = %s
```
Archives the student record before removal. The `Graduated_Student` table has no FK to `Student` so the archive survives.

---

#### Follow-up / Contact Parent
```sql
SELECT sf.Student_ID, sf.Fname, sf.Lname, sf.User_ID,
       sf.Parent_Name, sf.Parent_Email, sf.Parent_Phone
FROM v_student_full sf
WHERE sf.Student_ID = %s

-- Creates an in-app notification for the student
INSERT INTO Notification (User_ID, Title, Message, Type)
VALUES (%s, %s, %s, 'announcement')
```
An email is sent via SMTP (Mailpit) and a notification is also inserted for the student.

---

#### Expel from Subject (Teacher)
```sql
-- Authorization check
SELECT 1 FROM Teaches WHERE Emp_ID=%s AND Subject_ID=%s

-- Remove enrollment
DELETE FROM Enrollments
WHERE Student_ID=%s AND Subject_ID=%s [AND Semester=%s]
```

---

#### Enrollment Count for Subjects (Admin Students Page)
```sql
SELECT Student_ID, Subject_ID, Semester, Academic_Year, Status
FROM Enrollments ORDER BY Student_ID
```
Fetched once and mapped into a dict (`student_enrolled_map`) to avoid N+1 queries when rendering enrollment modals for each student.

---

### 3.4 Student Profile

#### Full Profile Data
```sql
SELECT * FROM v_student_full WHERE Student_ID = %s
```

---

#### Grade History
```sql
SELECT sub.Subject_Name, en.Final_Grade AS Grade, en.Semester
FROM Enrollments en
JOIN Subject sub ON en.Subject_ID = sub.Subject_ID
WHERE en.Student_ID = %s
ORDER BY en.Semester DESC, sub.Subject_Name
```

---

#### Assignment Submissions
```sql
SELECT su.Sub_ID, su.Submitted_At, su.Score, su.Feedback, su.File_Path,
       a.Title, a.Max_Score
FROM Submission su
JOIN Assignment a ON su.Assignment_ID = a.Assignment_ID
WHERE su.Student_ID = %s
ORDER BY su.Submitted_At DESC
```

---

#### Grade Average Summary
```sql
SELECT ROUND(AVG(Final_Grade),2) AS avg_grade, COUNT(*) AS grade_count
FROM Enrollments
WHERE Student_ID = %s AND Final_Grade IS NOT NULL
```

---

#### Attendance Rate
```sql
SELECT COUNT(*) AS total,
       SUM(CASE WHEN Present THEN 1 ELSE 0 END) AS present
FROM Attendance
WHERE Student_ID = %s
```
Rate calculated in Python: `(present / total) * 100`.

---

### 3.5 Teachers & Academic Management

#### List All Teachers (with subject count)
```sql
SELECT tf.Emp_ID, tf.Emp_FName, tf.Emp_LName, ...,
       COUNT(DISTINCT t.Subject_ID) AS subject_count
FROM v_teacher_full tf
LEFT JOIN Teaches t ON tf.Emp_ID = t.Emp_ID
WHERE (%s='' OR tf.Dept_Name = %s)
GROUP BY tf.Emp_ID
ORDER BY tf.Emp_FName, tf.Emp_LName
```

---

#### Add Teacher
```sql
INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
VALUES (%s,%s,%s,'teacher')

INSERT INTO Employee
(User_ID, Emp_FName, Emp_LName, Emp_Email, Emp_Phone,
 Employment_Date, Emp_Type, Dept_ID, Is_Supervisor)
VALUES (%s,%s,%s,%s,%s,%s,'instructor',%s,%s)

INSERT INTO Instructor (Emp_ID) VALUES (%s)
```
Three inserts in sequence; each uses the previous `lastrowid`.

---

#### Edit Teacher
```sql
UPDATE Employee
SET Emp_FName=%s, Emp_LName=%s, Emp_Email=%s, Emp_Phone=%s,
    Employment_Date=%s, Dept_ID=%s, Is_Supervisor=%s
WHERE Emp_ID = %s

UPDATE Users SET Full_Name=%s, Email=%s WHERE User_ID = %s
```

---

#### Delete Teacher
```sql
DELETE FROM Users WHERE User_ID = %s
```
Cascades to `Employee → Instructor`. `Teaches` and `Schedule_Entry.Emp_ID` use SET NULL/CASCADE so subject assignments are cleaned up automatically.

---

#### Add Subject
```sql
INSERT INTO Subject (Subject_Name, Subject_Level, Subject_Slots, Dept_ID)
VALUES (%s,%s,%s,%s)

INSERT IGNORE INTO Teaches (Emp_ID, Subject_ID) VALUES (%s,%s)
```

---

#### Assign Teacher to Subject
```sql
DELETE FROM Teaches WHERE Subject_ID = %s

INSERT INTO Teaches (Emp_ID, Subject_ID) VALUES (%s,%s)
```
Replaces the entire teacher assignment rather than appending — ensures one teacher per subject.

---

#### List Subjects (with teacher info)
```sql
SELECT s.Subject_ID, s.Subject_Name, s.Subject_Level, s.Subject_Slots,
       d.Dept_Name, e.Emp_FName, e.Emp_LName, e.Emp_ID
FROM Subject s
LEFT JOIN Department d ON s.Dept_ID = d.Dept_ID
LEFT JOIN Teaches t ON s.Subject_ID = t.Subject_ID
LEFT JOIN Employee e ON t.Emp_ID = e.Emp_ID
ORDER BY s.Subject_Name
```

---

### 3.6 Assignments

#### Student View (with own submission joined)
```sql
SELECT a.Assignment_ID, a.Title, a.Description, a.Due_Date, a.Max_Score,
       a.File_Path, a.Status, s.Subject_Name,
       CONCAT(e.Emp_FName,' ',e.Emp_LName) AS teacher_name,
       su.Sub_ID, su.Score, su.Feedback, su.Submitted_At,
       su.File_Path AS solution_file
FROM Assignment a
JOIN Subject s ON a.Subject_ID = s.Subject_ID
JOIN Enrollments en ON a.Subject_ID = en.Subject_ID AND en.Student_ID = %s
LEFT JOIN Employee e ON a.Emp_ID = e.Emp_ID
LEFT JOIN Submission su
       ON a.Assignment_ID = su.Assignment_ID AND su.Student_ID = %s
ORDER BY a.Due_Date IS NULL, a.Due_Date ASC
```
The `LEFT JOIN Submission` with `AND su.Student_ID = %s` attaches each student's own submission status in a single query — no N+1.

---

#### Teacher View (with submission counts)
```sql
SELECT a.*, s.Subject_Name,
       COUNT(DISTINCT sub.Sub_ID) AS submitted,
       (SELECT COUNT(*) FROM Enrollments WHERE Subject_ID = a.Subject_ID) AS total_students
FROM Assignment a
JOIN Subject s ON a.Subject_ID = s.Subject_ID
LEFT JOIN Employee e ON a.Emp_ID = e.Emp_ID
LEFT JOIN Submission sub ON a.Assignment_ID = sub.Assignment_ID
WHERE a.Emp_ID = %s
GROUP BY a.Assignment_ID
ORDER BY a.Due_Date IS NULL, a.Due_Date ASC
```

---

#### Create Assignment + Notify Students
```sql
INSERT INTO Assignment
(Title, Description, Subject_ID, Emp_ID, Due_Date, Max_Score, File_Path, Status)
VALUES (%s,%s,%s,%s,%s,%s,%s,'Active')

-- Bulk notify all students in one INSERT…SELECT (no Python loop)
INSERT INTO Notification (User_ID, Title, Message, Type)
SELECT User_ID, 'New Assignment', %s, 'system'
FROM Student WHERE User_ID IS NOT NULL
```

---

#### Submit Assignment
```sql
INSERT INTO Submission (Assignment_ID, Student_ID, File_Path)
VALUES (%s,%s,%s)
```

---

#### Grade Submission
```sql
UPDATE Submission SET Score=%s, Feedback=%s WHERE Sub_ID = %s

-- Flip to "Grading" only if still "Active" — won't overwrite "Published"/"Closed"
UPDATE Assignment SET Status='Grading'
WHERE Assignment_ID = (SELECT Assignment_ID FROM Submission WHERE Sub_ID=%s)
  AND Status = 'Active'

-- Notify the student
INSERT INTO Notification (User_ID, Title, Message, Type)
VALUES (%s, 'Assignment Graded', %s, 'grade')
```

---

### 3.7 Gradebook

#### Load Subject List (Teacher)
```sql
SELECT s.Subject_ID, s.Subject_Name
FROM Subject s
JOIN Teaches t ON s.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s
ORDER BY s.Subject_Name
```

---

#### Load Student Grades for a Subject
```sql
SELECT e.Enrollment_ID, e.Student_ID, e.Final_Grade, e.Semester,
       s.Fname, s.Lname, s.Level, s.Student_Email
FROM Enrollments e
JOIN Student s ON e.Student_ID = s.Student_ID
WHERE e.Subject_ID = %s
ORDER BY s.Fname, s.Lname
```

---

#### Save Grades
```sql
-- Authorization check
SELECT 1 FROM Teaches WHERE Emp_ID=%s AND Subject_ID=%s

-- Per student (loop in Python)
UPDATE Enrollments SET Final_Grade=%s
WHERE Enrollment_ID=%s AND Subject_ID=%s
```
Grades are stored in `Enrollments.Final_Grade` (not derived from submissions) — teacher has direct control.

---

### 3.8 Attendance

#### Load Schedule Entries for a Subject
```sql
SELECT se.Entry_ID, se.Day_Of_Week,
       TIME_FORMAT(se.Start_Time,'%H:%i') AS Start_T,
       TIME_FORMAT(se.End_Time,'%H:%i')   AS End_T
FROM Schedule_Entry se
WHERE se.Subject_ID = %s
ORDER BY se.Day_Of_Week, se.Start_Time
```
Used to populate the "time slot" dropdown in the attendance form.

---

#### Load Existing Attendance for a Date
```sql
SELECT a.Student_ID, a.Present
FROM Attendance a
JOIN Schedule_Entry se ON a.Entry_ID = se.Entry_ID
WHERE se.Subject_ID = %s AND a.Att_Date = %s
```

---

#### Save Attendance (Upsert)
```sql
-- Check existence
SELECT Att_ID FROM Attendance
WHERE Student_ID=%s AND Entry_ID=%s AND Att_Date=%s

-- Update if exists
UPDATE Attendance SET Present=%s WHERE Att_ID=%s

-- Insert if new
INSERT INTO Attendance (Student_ID, Entry_ID, Att_Date, Present)
VALUES (%s,%s,%s,%s)
```
This runs per student in a Python loop. Idempotent — re-submitting the same form updates rather than duplicates.

---

#### Attendance Summary (by Subject)
```sql
-- Teacher view (filtered to their subjects)
SELECT af.Subject_ID, af.Subject_Name,
       COUNT(DISTINCT af.Att_Date)                AS sessions,
       COUNT(af.Att_ID)                           AS total_records,
       SUM(CASE WHEN af.Present THEN 1 ELSE 0 END) AS present_count
FROM v_attendance_full af
JOIN Teaches t ON af.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s
GROUP BY af.Subject_ID
ORDER BY af.Subject_Name

-- Admin view (all subjects)
SELECT af.Subject_ID, af.Subject_Name, ...
FROM v_attendance_full af
GROUP BY af.Subject_ID
ORDER BY af.Subject_Name
```

---

### 3.9 Schedule

#### Admin — All Entries
```sql
SELECT Entry_ID, Day_Of_Week, Start_T, End_T, Semester, Academic_Year,
       Subject_Name, Subject_Level, Classroom_Name, Teacher_Name
FROM v_schedule_full
ORDER BY FIELD(Day_Of_Week,'Monday','Tuesday','Wednesday','Thursday',
               'Friday','Saturday','Sunday'), Start_T
```
`FIELD()` sorts weekdays in Mon→Sun order rather than alphabetically.

---

#### Teacher — Own Entries
```sql
SELECT ... FROM v_schedule_full WHERE Emp_ID = %s
ORDER BY FIELD(Day_Of_Week,...), Start_T
```

---

#### Student — Enrolled Subjects Only
```sql
SELECT sf.*
FROM v_schedule_full sf
WHERE sf.Subject_ID IN (
    SELECT Subject_ID FROM Enrollments WHERE Student_ID = %s
)
ORDER BY FIELD(sf.Day_Of_Week,...), sf.Start_T
```

---

#### Add Schedule Entry
```sql
INSERT INTO Schedule_Entry
(Subject_ID, Emp_ID, Classroom_ID, Semester, Academic_Year,
 Day_Of_Week, Start_Time, End_Time)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)

-- Keep Teaches junction in sync
INSERT IGNORE INTO Teaches (Emp_ID, Subject_ID) VALUES (%s,%s)
```
The UNIQUE constraint on `(Classroom_ID, Day_Of_Week, Start_Time, Semester, Academic_Year)` makes `execute()` return `None` on conflict, which the route handler detects and flashes an error for.

---

#### Delete Schedule Entry
```sql
DELETE FROM Schedule_Entry WHERE Entry_ID = %s
```

---

### 3.10 Enrollment Management

#### Enroll Student in Subject (Admin)
```sql
-- Prevent duplicate
SELECT Enrollment_ID FROM Enrollments
WHERE Student_ID=%s AND Subject_ID=%s AND Semester=%s

-- Enroll
INSERT INTO Enrollments (Student_ID, Subject_ID, Semester, Academic_Year, Status)
VALUES (%s,%s,%s,%s,%s)
```

---

#### Unenroll Student from Subject
```sql
DELETE FROM Enrollments
WHERE Student_ID=%s AND Subject_ID=%s AND Semester=%s
```

---

#### My Subjects (Student)
```sql
SELECT ed.Subject_ID, ed.Subject_Name, ed.Subject_Level,
       ed.Dept_Name, ed.Final_Grade AS Grade, ed.Semester,
       ed.Teacher_Name
FROM v_enrollment_detail ed
WHERE ed.Student_ID = %s
ORDER BY ed.Semester DESC, ed.Subject_Name
```

---

### 3.11 Analytics

#### Overview Stats
```sql
SELECT ROUND(AVG(Final_Grade),1)             AS avg_grade,
       (SELECT COUNT(*) FROM Student)        AS total_students,
       (SELECT COUNT(*) FROM Instructor)     AS total_teachers,
       (SELECT COUNT(*) FROM Assignment)     AS total_assignments
FROM Enrollments
WHERE Final_Grade IS NOT NULL
```
Scalar subqueries in the SELECT clause pull the three counts in a single round-trip.

---

#### Grade Distribution (for Doughnut Chart)
```sql
SELECT
  SUM(CASE WHEN Final_Grade >= 90              THEN 1 ELSE 0 END) AS A_count,
  SUM(CASE WHEN Final_Grade >= 80 AND < 90     THEN 1 ELSE 0 END) AS B_count,
  SUM(CASE WHEN Final_Grade >= 70 AND < 80     THEN 1 ELSE 0 END) AS C_count,
  SUM(CASE WHEN Final_Grade >= 60 AND < 70     THEN 1 ELSE 0 END) AS D_count,
  SUM(CASE WHEN Final_Grade <  60              THEN 1 ELSE 0 END) AS F_count
FROM Enrollments
WHERE Final_Grade IS NOT NULL
```
All five grade buckets computed in a single pass — no separate queries per grade.

---

#### Subject Performance (for Bar Chart)
```sql
SELECT sub.Subject_Name,
       ROUND(AVG(en.Final_Grade),1) AS avg_grade
FROM Enrollments en
JOIN Subject sub ON en.Subject_ID = sub.Subject_ID
WHERE en.Final_Grade IS NOT NULL
GROUP BY sub.Subject_ID
ORDER BY avg_grade DESC
```

---

#### Assignment Completion Rate (for Line Chart)
```sql
SELECT a.Title,
       COUNT(su.Sub_ID) AS submitted,
       (SELECT COUNT(*) FROM Student) AS total_students
FROM Assignment a
LEFT JOIN Submission su ON a.Assignment_ID = su.Assignment_ID
GROUP BY a.Assignment_ID
ORDER BY a.Created_At DESC
LIMIT 8
```
Completion % = `(submitted / total_students) * 100` — computed in Python.

---

#### Teacher Activity (for Bar Chart)
```sql
SELECT CONCAT(e.Emp_FName,' ',e.Emp_LName) AS teacher_name,
       COUNT(a.Assignment_ID) AS assignments_created
FROM Employee e
JOIN Instructor i ON e.Emp_ID = i.Emp_ID
LEFT JOIN Assignment a ON i.Emp_ID = a.Emp_ID
GROUP BY e.Emp_ID
ORDER BY assignments_created DESC
LIMIT 8
```

---

#### Monthly Trend (for Line Chart)
```sql
SELECT DATE_FORMAT(Created_At, '%Y-%m') AS month_label,
       COUNT(*) AS total
FROM Assignment
GROUP BY DATE_FORMAT(Created_At, '%Y-%m')
ORDER BY month_label ASC
LIMIT 12
```

---

### 3.12 Notifications

#### Fetch Notifications
```sql
SELECT * FROM Notification
WHERE User_ID = %s OR User_ID IS NULL
ORDER BY Created_At DESC
```
`User_ID IS NULL` fetches broadcast notifications visible to everyone.

---

#### Mark All as Read
```sql
UPDATE Notification SET Is_Read = TRUE
WHERE User_ID = %s OR User_ID IS NULL
```

---

#### Create Notification (Admin)
```sql
INSERT INTO Notification (User_ID, Title, Message, Type)
VALUES (%s,%s,%s,%s)
```
`User_ID = NULL` for broadcasts.

---

### 3.13 Classrooms

#### List Classrooms
```sql
SELECT c.Classroom_ID, c.Classroom_Name, c.Capacity, c.Building, c.Floor,
       COUNT(se.Entry_ID) AS slot_count
FROM Classroom c
LEFT JOIN Schedule_Entry se ON c.Classroom_ID = se.Classroom_ID
[WHERE clauses for search/building/floor filters]
GROUP BY c.Classroom_ID
ORDER BY c.Building, c.Floor, c.Classroom_Name
```

---

#### Add / Edit / Delete Classroom
```sql
-- Add
INSERT INTO Classroom (Classroom_Name, Capacity, Building, Floor)
VALUES (%s,%s,%s,%s)

-- Edit
UPDATE Classroom SET Classroom_Name=%s, Capacity=%s, Building=%s, Floor=%s
WHERE Classroom_ID = %s

-- Safety check before delete
SELECT COUNT(*) AS c FROM Schedule_Entry WHERE Classroom_ID = %s

-- Delete
DELETE FROM Classroom WHERE Classroom_ID = %s
```
A classroom with active schedule entries cannot be deleted — the safety count check guards this.

---

### 3.14 Departments

#### List Departments
```sql
SELECT d.Dept_ID, d.Dept_Name, d.Dept_Head_ID,
       CONCAT(e.Emp_FName,' ',e.Emp_LName) AS Dept_Head_Name
FROM Department d
LEFT JOIN Employee e ON d.Dept_Head_ID = e.Emp_ID
[WHERE d.Dept_Name LIKE %s]
ORDER BY d.Dept_Name
```

---

#### Add / Edit / Delete Department
```sql
-- Duplicate check
SELECT Dept_ID FROM Department WHERE Dept_Name = %s

-- Add
INSERT INTO Department (Dept_Name, Dept_Head_ID) VALUES (%s,%s)

-- Edit
UPDATE Department SET Dept_Name=%s, Dept_Head_ID=%s WHERE Dept_ID = %s

-- Safety check before delete
SELECT COUNT(*) AS c FROM Employee WHERE Dept_ID = %s
SELECT COUNT(*) AS c FROM Subject WHERE Dept_ID = %s

-- Delete
DELETE FROM Department WHERE Dept_ID = %s
```

---

### 3.15 Registration Review (Admin)

#### UNION Query (used across all registration routes)
```sql
SELECT
    Student_Reg_ID AS Reg_ID, 'student' AS Applicant_Type,
    Full_Name, Birth_Date, Gender, Nationality, Email, Phone,
    Grade_Applied, Parent_Name, Parent_Phone, Parent_Email,
    Address, Previous_School, Birth_Certificate, Student_Photo,
    Previous_Transcript, NULL AS Department, NULL AS Qualification,
    NULL AS Specialization, NULL AS Employment_Date, Status, Submitted_At
FROM Student_Registration
UNION ALL
SELECT
    Teacher_Reg_ID AS Reg_ID, 'teacher' AS Applicant_Type,
    Full_Name, NULL, NULL, NULL, Contact_Email, Phone_Number,
    NULL, NULL, NULL, NULL,
    Address, NULL, NULL, NULL,
    NULL, Department, Qualification,
    Specialization, Available_Start_Date, Status, Submitted_At
FROM Teacher_Registration
```
Normalizes two differently-structured tables into one consistent shape. `UNION ALL` (not `UNION`) preserves duplicates and is faster.

---

#### Approve Registration → Create Account
On approval, the app calls either `create_student_from_registration()` or `create_teacher_from_registration()`, which run the full insert chains documented in [3.3](#33-students) and [3.5](#35-teachers--academic-management) respectively, then send welcome email with temp credentials.

```sql
-- Update registration status after approval/rejection
UPDATE Student_Registration SET Status=%s WHERE Student_Reg_ID=%s
UPDATE Teacher_Registration SET Status=%s WHERE Teacher_Reg_ID=%s
```

---

### 3.16 AI Assistant

The AI assistant is admin-only. It uses the Google Gemini API to convert natural language to SQL, then executes and returns the results.

#### Schema Provided to Gemini
The `DB_SCHEMA` string in `app.py` describes all tables and views to the model, prompting it to return only `{"sql": "...", "explanation": "..."}`.

#### Security Validation
```python
# Only SELECT statements allowed
if not re.match(r"^select\b", sql_query, re.IGNORECASE):
    return error

# Block any DML/DDL keywords
if re.search(r"\b(insert|update|delete|drop|alter|truncate|create|replace)\b", sql_query, re.IGNORECASE):
    return error
```

#### Fallback Patterns (when Gemini is unavailable)
| Keyword Pattern | Query Produced |
|----------------|---------------|
| "top" + "student" | Top 10 students by avg grade |
| "failed" + "math" | Students with grade < 60 in math subjects |
| "best" + "class/subject" | Subjects ranked by avg grade |
| "submitted this week" | Submissions in current calendar week |
| (default) | Last 50 students by enrollment date |

---

### 3.17 Activity Logs

#### Insert Log Entry
```python
def log_activity(action, table_name=None):
    execute(
        "INSERT INTO Activity_Logs (User_ID, Action, Table_Name) VALUES (%s, %s, %s)",
        (user_id, action, table_name)
    )
```
Called manually after significant operations (add/edit/delete student, graduate, classroom changes, etc.).

---

#### Fetch Logs (Admin)
```sql
SELECT l.*, u.Full_Name, u.Role
FROM Activity_Logs l
LEFT JOIN Users u ON l.User_ID = u.User_ID
ORDER BY l.Action_Time DESC
LIMIT 500
```

---

## 4. Access Control & Decorators

| Decorator | Allowed Roles | Redirect on Fail |
|-----------|--------------|-----------------|
| `@login_required` | Any authenticated | `/login` |
| `@admin_required` | `admin` only | `/dashboard` (403 flash) |
| `@teacher_or_admin_required` | `teacher`, `admin` | `/dashboard` |
| `@student_required` | `student` only | `/dashboard` |
| `@role_required(*roles)` | Configurable list | `/dashboard` |

All decorators check `session["user_id"]` first; unauthenticated users always go to `/login`.

---

## 5. Helper Functions Reference

| Function | Purpose |
|----------|---------|
| `log_activity(action, table)` | Inserts an audit log row |
| `inject_user()` | Context processor; exposes `current_user`, `user_name`, `user_role`, `user_photo` to all templates |
| `count(sql, params)` | Shorthand `query()` wrapper that returns a single integer from a `COUNT(*)` query |
| `safe_filename(field_name)` | Reads a file upload from the request, saves it to `static/uploads/`, returns the relative path |
| `split_name(full_name)` | Splits "John Doe" into `("John", "Doe")` |
| `year_label(value)` | Returns grade level string or `"No year assigned"` |
| `year_sort_key(label)` | Sort key that puts KG before Grade 1, Grade 1 before Grade 2, etc. |
| `group_by_year(rows, key)` | Groups a list of dicts by grade level, sorted with `year_sort_key` |
| `ensure_department(name)` | Upsert a department by name; returns `Dept_ID` |
| `ensure_classroom(name, ...)` | Upsert a classroom by name; returns `Classroom_ID` |
| `ensure_parent(name, phone, email)` | Upsert a parent by name+email; returns `Parent_ID` |
| `current_student_id()` | Returns `Student_ID` for the logged-in student, or `None` |
| `current_teacher_id()` | Returns `Emp_ID` for the logged-in teacher, or `None` |
| `login_user(user)` | Clears session and sets `user_id`, `email`, `name`, `role` |
| `verify_password_and_upgrade_if_needed(user, password)` | Verifies bcrypt or legacy scrypt hash; upgrades scrypt to bcrypt on success |
| `generate_temp_password(length=12)` | Returns a cryptographically random 12-char password |
| `slugify_email_part(value)` | Converts a name to a lowercase dot-separated slug for email generation |
| `generate_temp_login_email(name, role)` | Generates a unique `role.name@galala.local` email |
| `create_student_from_registration(reg)` | Full pipeline: create Users → Parents → Student from a registration dict |
| `create_teacher_from_registration(reg)` | Full pipeline: create Users → Employee → Instructor |
| `registration_contact_email(reg)` | Returns the right email (parent for students, personal for teachers) |
| `fallback_ai(question)` | Returns a hardcoded SQL dict when Gemini is unavailable |
| `generate_sql(question)` | Calls Gemini API or falls back; returns `{sql, explanation}` |

---

## 6. Key SQL Patterns

### Empty String as "No Filter"
Rather than building dynamic SQL strings, all filter queries pass empty strings for inactive filters. The condition `(%s='' OR column = %s)` evaluates to `TRUE` when the param is `''`.

```sql
WHERE (%s='' OR sf.Status = %s)
--      ^^ empty = no filter
```

### Null-Last Ordering
```sql
ORDER BY a.Due_Date IS NULL, a.Due_Date ASC
```
`IS NULL` returns `1` for NULL rows and `0` for non-NULL, so NULL dates sort after real dates — no `CASE` required.

### Single-Pass Grade Bucketing
```sql
SUM(CASE WHEN Final_Grade >= 90 THEN 1 ELSE 0 END) AS A_count
```
All five A/B/C/D/F counts computed in one query pass.

### Scalar Subqueries for Mixed Aggregates
```sql
SELECT ROUND(AVG(Final_Grade),1) AS avg_grade,
       (SELECT COUNT(*) FROM Student) AS total_students,
       (SELECT COUNT(*) FROM Instructor) AS total_teachers
FROM Enrollments WHERE Final_Grade IS NOT NULL
```
Avoids multiple round-trips while mixing aggregate and count data.

### `INSERT IGNORE` for Junction Tables
```sql
INSERT IGNORE INTO Teaches (Emp_ID, Subject_ID) VALUES (%s,%s)
```
Silent no-op if the row already exists; no need to check first.

### `FIELD()` for Custom Sort Order
```sql
ORDER BY FIELD(Day_Of_Week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
```
Sorts days in human calendar order, not alphabetically.

### `DATE_FORMAT` Grouping
```sql
GROUP BY DATE_FORMAT(Created_At, '%Y-%m')
```
Groups timestamps by year-month for trend charts without truncating precision in stored data.

### Attendance Upsert Pattern
```sql
-- Check
SELECT Att_ID FROM Attendance WHERE Student_ID=%s AND Entry_ID=%s AND Att_Date=%s
-- Then: UPDATE if found, INSERT if not
```
Idempotent — re-submitting the same attendance form is safe.

### Bulk Notification via INSERT…SELECT
```sql
INSERT INTO Notification (User_ID, Title, Message, Type)
SELECT User_ID, 'New Assignment', %s, 'system'
FROM Student WHERE User_ID IS NOT NULL
```
Notifies all students in a single SQL statement instead of a Python loop.

---

*Documentation generated for Galala SIS v1.0 — Flask + MySQL*
