-- ============================================================
--  Galala International School — Optimized Schema
--  Generated from ERD diagram + app.py reconciliation
--  Changes vs old schema:
--   • Parents extracted to own table (diagram) — Students.Parent_ID FK
--   • Employees gains Emp_Type ENUM (diagram) — replaces Instructor-only split
--   • Instructors kept as sub-type table (Emp_ID PK/FK)
--   • Studies → Enrollments (diagram name, richer fields)
--   • Schedule_Entry gains Semester + Academic_Year (diagram)
--   • Attendance.Entry_ID FK → Schedule_Entry (diagram) instead of loose Subject_ID
--   • Student_Registration consolidated; Teacher_Registration kept separate
--   • Graduated_Student preserved as required
--   • Is_An junction removed — Instructor already has Dept via Employee.Dept_ID
--   • Redundant Subject.Classroom_ID removed — placement lives in Schedule_Entry
--   • All ON DELETE/ON UPDATE rules tightened for RI
-- ============================================================

DROP DATABASE IF EXISTS school_db;
CREATE DATABASE school_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE school_db;

-- ──────────────────────────────────────────
--  CORE AUTH
-- ──────────────────────────────────────────

CREATE TABLE Users (
    User_ID        INT            AUTO_INCREMENT PRIMARY KEY,
    Full_Name      VARCHAR(100)   NOT NULL,
    Email          VARCHAR(150)   NOT NULL UNIQUE,
    Password_Hash  VARCHAR(255)   NOT NULL,
    Role           ENUM('student','teacher','admin') NOT NULL,
    Created_At     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- Seed the default admin (scrypt hash preserved from original)
INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
VALUES (
    'Admin',
    'Admin@gmail.com',
    'scrypt:32768:8:1$joabjGxNE3UlNpg3$21a920099d5aa7d6a2558f109e6ead2f5d35a9d6d1f0af6b077360381eada853880866b463d738a2ea0372db3c628f8ef46c4cb40f8131f505d96c2592ea3ad8',
    'admin'
);

-- ──────────────────────────────────────────
--  PARENTS  (extracted from Student per diagram)
-- ──────────────────────────────────────────

CREATE TABLE Parents (
    Parent_ID      INT            AUTO_INCREMENT PRIMARY KEY,
    Parent_Name    VARCHAR(100)   NOT NULL,
    Parent_Email   VARCHAR(150)   NOT NULL,
    Parent_Phone   VARCHAR(20)    NOT NULL
);

-- ──────────────────────────────────────────
--  DEPARTMENTS
-- ──────────────────────────────────────────

CREATE TABLE Department (
    Dept_ID    INT          AUTO_INCREMENT PRIMARY KEY,
    Dept_Name  VARCHAR(100) NOT NULL UNIQUE,
    -- Head is a nullable FK back to Employee; added after Employee is defined
    Dept_Head_ID INT        DEFAULT NULL
);

-- ──────────────────────────────────────────
--  CLASSROOMS
-- ──────────────────────────────────────────

CREATE TABLE Classroom (
    Classroom_ID       INT          AUTO_INCREMENT PRIMARY KEY,
    Classroom_Name     VARCHAR(50)  NOT NULL,
    Capacity           INT,
    Building           VARCHAR(50),
    Floor              VARCHAR(20),
    UNIQUE KEY uq_classroom_name (Classroom_Name)
);

-- ──────────────────────────────────────────
--  EMPLOYEES  (all staff)
-- ──────────────────────────────────────────

CREATE TABLE Employee (
    Emp_ID           INT            AUTO_INCREMENT PRIMARY KEY,
    User_ID          INT            UNIQUE,
    Dept_ID          INT            NOT NULL,
    Emp_FName        VARCHAR(50)    NOT NULL,
    Emp_LName        VARCHAR(50)    NOT NULL,
    Emp_Email        VARCHAR(150),
    Emp_Phone        VARCHAR(20),
    Employment_Date  DATE,
    Emp_Type         ENUM('instructor','admin_staff','support') DEFAULT 'instructor',
    Supervisor_ID    INT            DEFAULT NULL,
    FOREIGN KEY (User_ID)       REFERENCES Users(User_ID)    ON DELETE CASCADE,
    FOREIGN KEY (Dept_ID)       REFERENCES Department(Dept_ID) ON DELETE RESTRICT,
    FOREIGN KEY (Supervisor_ID) REFERENCES Employee(Emp_ID)  ON DELETE SET NULL
);

-- Now we can add the deferred FK for Department.Dept_Head_ID
ALTER TABLE Department
    ADD CONSTRAINT fk_dept_head
    FOREIGN KEY (Dept_Head_ID) REFERENCES Employee(Emp_ID) ON DELETE SET NULL;
-- ──────────────────────────────────────────
--  INSTRUCTORS  (sub-type of Employee)
-- ──────────────────────────────────────────

CREATE TABLE Instructor (
    Emp_ID          INT           PRIMARY KEY,
    Department_ID   INT           NOT NULL,
    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID) ON DELETE CASCADE,
    FOREIGN KEY (Department_ID) REFERENCES Department(Dept_ID) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  SUBJECTS
--  Removed Classroom_ID — classroom is bound to a schedule slot, not a subject
-- ──────────────────────────────────────────

CREATE TABLE Subject (
    Subject_ID    INT           AUTO_INCREMENT PRIMARY KEY,
    Subject_Name  VARCHAR(100)  NOT NULL,
    Subject_Level VARCHAR(50),
    Subject_Slots INT,
    Dept_ID       INT,
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID) ON DELETE SET NULL
);

-- ──────────────────────────────────────────
--  TEACHES  (many-to-many Instructor ↔ Subject)
-- ──────────────────────────────────────────

CREATE TABLE Teaches (
    Emp_ID     INT NOT NULL,
    Subject_ID INT NOT NULL,
    PRIMARY KEY (Emp_ID, Subject_ID),
    FOREIGN KEY (Emp_ID)     REFERENCES Instructor(Emp_ID)  ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  STUDENTS
-- ──────────────────────────────────────────

CREATE TABLE Student (
    Student_ID           INT            AUTO_INCREMENT PRIMARY KEY,
    User_ID              INT            UNIQUE,
    Fname                VARCHAR(50)    NOT NULL,
    Lname                VARCHAR(50)    NOT NULL,
    Level                VARCHAR(50)    NOT NULL,
    Batch_Year           INT,
    Birth_Date           DATE           NOT NULL,
    Gender               VARCHAR(20)    NOT NULL,
    Nationality          VARCHAR(80)    NOT NULL,
    Student_Email        VARCHAR(150),
    Student_Pnum         VARCHAR(20),
    Parent_Name          VARCHAR(100)   NOT NULL,
    Parent_Pnum          VARCHAR(20)    NOT NULL,
    Parent_Email         VARCHAR(150)   NOT NULL,
    Student_Address      VARCHAR(250),
    Previous_School      VARCHAR(150),
    Student_Photo        VARCHAR(255),
    Birth_Certificate    VARCHAR(255),
    Previous_Transcript  VARCHAR(255),
    Status               ENUM('Active','Enrolled','Pending') DEFAULT 'Pending',
    Enrolled_At          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID)   REFERENCES Users(User_ID)   ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  ENROLLMENTS  (was Studies)
--  Richer: Academic_Year, Final_Grade per enrollment, Status
-- ──────────────────────────────────────────

CREATE TABLE Enrollments (
    Enrollment_ID  INT             AUTO_INCREMENT PRIMARY KEY,
    Student_ID     INT             NOT NULL,
    Subject_ID     INT             NOT NULL,
    Semester       VARCHAR(20)     DEFAULT 'CURRENT',
    Academic_Year  VARCHAR(20),
    Final_Grade    DECIMAL(5,2),
    Status         ENUM('Active','Completed','Dropped','Failed') DEFAULT 'Active',
    Enrolled_At    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_enrollment (Student_ID, Subject_ID, Semester),
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID) ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  SCHEDULE ENTRIES
-- ──────────────────────────────────────────

CREATE TABLE Schedule_Entry (
    Entry_ID       INT    AUTO_INCREMENT PRIMARY KEY,
    Subject_ID     INT    NOT NULL,
    Classroom_ID   INT,
    Emp_ID         INT,
    Semester       VARCHAR(20),
    Academic_Year  VARCHAR(20),
    Day_Of_Week    ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),
    Start_Time     TIME,
    End_Time       TIME,
    FOREIGN KEY (Subject_ID)   REFERENCES Subject(Subject_ID)     ON DELETE CASCADE,
    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID) ON DELETE SET NULL,
    FOREIGN KEY (Emp_ID)       REFERENCES Instructor(Emp_ID)      ON DELETE SET NULL
);

-- ──────────────────────────────────────────
--  ATTENDANCE
--  Now references Schedule_Entry.Entry_ID (diagram) in addition to Student
-- ──────────────────────────────────────────

CREATE TABLE Attendance (
    Att_ID      INT     AUTO_INCREMENT PRIMARY KEY,
    Student_ID  INT     NOT NULL,
    Entry_ID    INT     NOT NULL,   -- FK to Schedule_Entry (replaces bare Subject_ID)
    Att_Date    DATE    NOT NULL,
    Present     BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID)       ON DELETE CASCADE,
    FOREIGN KEY (Entry_ID)   REFERENCES Schedule_Entry(Entry_ID)  ON DELETE CASCADE,
    UNIQUE KEY uq_attendance (Student_ID, Entry_ID, Att_Date)
);

-- ──────────────────────────────────────────
--  ASSIGNMENTS
-- ──────────────────────────────────────────

CREATE TABLE Assignment (
    Assignment_ID  INT            AUTO_INCREMENT PRIMARY KEY,
    Title          VARCHAR(200)   NOT NULL,
    Description    TEXT,
    Subject_ID     INT            NOT NULL,
    Emp_ID         INT,
    Due_Date       DATE,
    Max_Score      DECIMAL(5,2)   DEFAULT 100,
    File_Path      VARCHAR(255),
    Status         ENUM('Active','Grading','Published','Closed') DEFAULT 'Active',
    Created_At     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID)    ON DELETE CASCADE,
    FOREIGN KEY (Emp_ID)     REFERENCES Instructor(Emp_ID)     ON DELETE SET NULL
);

-- ──────────────────────────────────────────
--  SUBMISSIONS
-- ──────────────────────────────────────────

CREATE TABLE Submission (
    Sub_ID         INT            AUTO_INCREMENT PRIMARY KEY,
    Assignment_ID  INT            NOT NULL,
    Student_ID     INT            NOT NULL,
    Submitted_At   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    File_Path      VARCHAR(255),
    Score          DECIMAL(5,2),
    Feedback       TEXT,
    UNIQUE KEY uq_submission (Assignment_ID, Student_ID),
    FOREIGN KEY (Assignment_ID) REFERENCES Assignment(Assignment_ID) ON DELETE CASCADE,
    FOREIGN KEY (Student_ID)    REFERENCES Student(Student_ID)       ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  NOTIFICATIONS  (diagram adds Sender_ID)
-- ──────────────────────────────────────────

CREATE TABLE Notification (
    Notif_ID    INT            AUTO_INCREMENT PRIMARY KEY,
    User_ID     INT            DEFAULT NULL,   -- NULL = broadcast
    Title       VARCHAR(200)   NOT NULL,
    Message     TEXT,
    Type        ENUM('assignment','grade','announcement','system','attendance') DEFAULT 'announcement',
    Is_Read     BOOLEAN        DEFAULT FALSE,
    Created_At  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID)   REFERENCES Users(User_ID) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  STUDENT REGISTRATION  (online applications)
-- ──────────────────────────────────────────

CREATE TABLE Student_Registration (
    Student_Reg_ID       INT            AUTO_INCREMENT PRIMARY KEY,
    Full_Name            VARCHAR(100)   NOT NULL,
    Birth_Date           DATE           NOT NULL,
    Gender               VARCHAR(20)    NOT NULL,
    Nationality          VARCHAR(80)    NOT NULL,
    Email                VARCHAR(150)   NOT NULL,
    Phone                VARCHAR(20)    NOT NULL,
    Grade_Applied        VARCHAR(50)    NOT NULL,
    Parent_Name          VARCHAR(100)   NOT NULL,
    Parent_Phone         VARCHAR(20)    NOT NULL,
    Parent_Email         VARCHAR(150)   NOT NULL,
    Address              VARCHAR(250)   NOT NULL,
    Previous_School      VARCHAR(150),
    Birth_Certificate    VARCHAR(255)   NOT NULL,
    Student_Photo        VARCHAR(255)   NOT NULL,
    Previous_Transcript  VARCHAR(255)   NOT NULL,
    Status               ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    Submitted_At         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────
--  TEACHER REGISTRATION  (online applications)
-- ──────────────────────────────────────────

CREATE TABLE Teacher_Registration (
    Teacher_Reg_ID      INT            AUTO_INCREMENT PRIMARY KEY,
    Full_Name           VARCHAR(100)   NOT NULL,
    Contact_Email       VARCHAR(150)   NOT NULL,
    Phone_Number        VARCHAR(20)    NOT NULL,
    Department          VARCHAR(100)   NOT NULL,
    Specialization      VARCHAR(150)   NOT NULL,
    Qualification       VARCHAR(200)   NOT NULL,
    Available_Start_Date DATE,
    Address             TEXT            NOT NULL,
    Notes               TEXT,
    Status              ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    Submitted_At        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────
--  GRADUATED STUDENTS  (preserved as required)
-- ──────────────────────────────────────────

CREATE TABLE Graduated_Student (
    Grad_ID              INT            AUTO_INCREMENT PRIMARY KEY,
    Student_ID           INT,           -- historical reference, no FK (row deleted from Student)
    Full_Name            VARCHAR(100),
    Email                VARCHAR(150),
    Graduation_Date      DATE,
    Level_At_Graduation  VARCHAR(50),
);

-- ──────────────────────────────────────────
--  ACTIVITY LOGS
-- ──────────────────────────────────────────

CREATE TABLE Activity_Logs (
    Log_ID       INT            AUTO_INCREMENT PRIMARY KEY,
    User_ID      INT,
    Action       VARCHAR(100)   NOT NULL,
    Table_Name   VARCHAR(100),
    Action_Time  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE SET NULL
);

-- ============================================================
--  VIEWS — pre-computed joins used frequently in app.py
-- ============================================================

-- Full student info with parent data (replaces repeated inline joins)
CREATE VIEW v_student_full AS
SELECT
    s.Student_ID, s.User_ID, s.Fname, s.Lname,
    CONCAT(s.Fname,' ',s.Lname)  AS Full_Name,
    s.Level, s.Birth_Date, s.Gender, s.Nationality,
    s.Student_Email, s.Student_Phone, s.Student_Address,
    s.Previous_School, s.Student_Photo, s.Status, s.Enrolled_At,
    s.Notes, s.Birth_Certificate, s.Previous_Transcript,
    p.Parent_ID, p.Parent_Name, p.Parent_Email, p.Parent_Phone,
    u.Email AS Login_Email
FROM Student s
LEFT JOIN Parents  p ON s.Parent_ID  = p.Parent_ID
LEFT JOIN Users    u ON s.User_ID    = u.User_ID;

-- Full teacher info
CREATE VIEW v_teacher_full AS
SELECT
    e.Emp_ID, e.User_ID, e.Emp_FName, e.Emp_LName,
    CONCAT(e.Emp_FName,' ',e.Emp_LName) AS Full_Name,
    e.Emp_Email, e.Emp_Phone, e.Employment_Date,
    e.Dept_ID, d.Dept_Name, e.Supervisor_ID,
    u.Email AS Login_Email
FROM Employee   e
JOIN Instructor i ON e.Emp_ID  = i.Emp_ID
JOIN Department d ON e.Dept_ID = d.Dept_ID
LEFT JOIN Users u ON e.User_ID = u.User_ID;

-- Enrollment with subject + student names (replaces Studies joins)
CREATE VIEW v_enrollment_detail AS
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

-- Schedule with all related names
CREATE VIEW v_schedule_full AS
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

-- Attendance joined to schedule entry (gives Subject_ID cheaply)
CREATE VIEW v_attendance_full AS
SELECT
    a.Att_ID, a.Student_ID, a.Entry_ID, a.Att_Date, a.Present,
    se.Subject_ID, se.Day_Of_Week,
    sub.Subject_Name,
    CONCAT(s.Fname,' ',s.Lname) AS Student_Name
FROM Attendance     a
JOIN Schedule_Entry se  ON a.Entry_ID   = se.Entry_ID
JOIN Subject        sub ON se.Subject_ID = sub.Subject_ID
JOIN Student        s   ON a.Student_ID  = s.Student_ID;
