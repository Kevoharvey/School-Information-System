DROP DATABASE school_db;
CREATE DATABASE school_db;
USE school_db;
-- ============================================================
--  Entities: Classroom, Subject, Student, Employee, Department, Instructor
--  Relationships: Is_In, Studies, Teaches, Is_An, Works_At, Supervisor
-- ============================================================

CREATE TABLE Department (
    Dept_ID INT PRIMARY KEY,
    Dept_Name VARCHAR(100) NOT NULL,
    Dept_Head VARCHAR(100)            -- name of head; link to Employee later if needed
);

-- ------------------------------------------------------------
-- EMPLOYEE
-- Composite attribute: Emp_Name → Emp_FName + Emp_Lname
-- Multivalued attribute: Emp_pnum  → separate table
-- Self-referencing relationship: Supervisor (N:1)
-- ------------------------------------------------------------
CREATE TABLE Employee (
    Emp_ID INT PRIMARY KEY,
    Emp_FName VARCHAR(50) NOT NULL,
    Emp_Lname VARCHAR(50) NOT NULL,
    Employment_Date DATE,
    Supervisor_ID INT,                        -- self-ref FK (Supervisor relationship)
    Dept_ID INT NOT NULL,   -- Works_At relationship

    FOREIGN KEY (Supervisor_ID) REFERENCES Employee(Emp_ID),
    FOREIGN KEY (Dept_ID)       REFERENCES Department(Dept_ID)
);

-- Multivalued attribute: an employee can have multiple phone numbers
CREATE TABLE Employee_Phone (
    Emp_ID INT NOT NULL,
    Emp_pnum VARCHAR(20) NOT NULL,
    PRIMARY KEY (Emp_ID, Emp_pnum),
    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID)
            ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- INSTRUCTOR
-- Is_An: ISA / specialisation of Employee (1:1)
-- Qualification is a single-value attribute of Instructor
-- ------------------------------------------------------------
CREATE TABLE Instructor (
    Emp_ID INT PRIMARY KEY,    -- same PK as Employee
    Qualification VARCHAR(200),
    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID)
            ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- CLASSROOM
-- Composite attribute: Classroom_Location → Building + Floor
-- ------------------------------------------------------------
CREATE TABLE Classroom (
    Classroom_ID INT PRIMARY KEY,
    Classroom_Level VARCHAR(50),
    Classroom_Capacity INT,
    Classroom_Building VARCHAR(100),
    Classroom_Floor VARCHAR(20)
);

-- ------------------------------------------------------------
-- SUBJECT
-- Is_In relationship with Classroom (many subjects in one classroom)
-- ------------------------------------------------------------
CREATE TABLE Subject (
    Subject_ID INT PRIMARY KEY,
    Subject_Name VARCHAR(100) NOT NULL,
    Subject_Level VARCHAR(50),
    Subject_Slots INT,
    Classroom_ID INT,                            -- Is_In relationship
    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID)
);

-- ------------------------------------------------------------
-- STUDENT
-- Composite attributes: Name → Fname + Lname
--                       Address → City + Street + Building_Num
-- Derived attribute: Age (computed from Birth_Date, not stored)
-- ------------------------------------------------------------
CREATE TABLE Student (
    Student_ID INT PRIMARY KEY,
    Fname VARCHAR(50) NOT NULL,
    Lname VARCHAR(50) NOT NULL,
    Level VARCHAR(50),
    Birth_Date DATE,
    -- Age is DERIVED from Birth_Date; use a view or computed column:
    -- Age = TIMESTAMPDIFF(YEAR, Birth_Date, CURDATE())  [MySQL]
    Student_Email VARCHAR(150),
    -- Composite address components
    City VARCHAR(100),
    Street VARCHAR(150),
    Building_Num VARCHAR(20)
);
-- ------------------------------------------------------------
-- STUDIES  (Student ↔ Subject  with attribute: Grades)
-- Many-to-many relationship
-- ------------------------------------------------------------
CREATE TABLE Studies (
    Student_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    Grades DECIMAL(5, 2),
    PRIMARY KEY (Student_ID, Subject_ID),
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID)
        ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TEACHES  (Instructor ↔ Subject)
-- Many-to-many relationship (one instructor teaches many subjects;
-- one subject can be taught by many instructors)
-- ------------------------------------------------------------
CREATE TABLE Teaches (
    Emp_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    PRIMARY KEY (Emp_ID, Subject_ID),
    FOREIGN KEY (Emp_ID) REFERENCES Instructor(Emp_ID)
        ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID)
        ON DELETE CASCADE
);
CREATE TABLE Users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Full_Name VARCHAR(100) NOT NULL,
    Email VARCHAR(150) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Role ENUM('student', 'teacher') NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE Student
ADD COLUMN User_ID INT UNIQUE,
ADD CONSTRAINT fk_student_user
FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
ON DELETE CASCADE;

ALTER TABLE Employee
ADD COLUMN User_ID INT UNIQUE,
ADD CONSTRAINT fk_employee_user
FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
ON DELETE CASCADE;
