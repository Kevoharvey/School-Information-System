DROP DATABASE IF EXISTS school_db;
CREATE DATABASE school_db;
USE school_db;

-- ============================================================
-- Entities: Classroom, Subject, Student, Employee, Department, Instructor
-- Relationships: Is_In, Studies, Teaches, Is_An, Works_At, Supervisor
-- ============================================================

-- ------------------------------------------------------------
-- USERS
-- ------------------------------------------------------------
CREATE TABLE Users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Full_Name VARCHAR(100) NOT NULL,
    Email VARCHAR(150) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Role ENUM('student', 'teacher', 'admin') NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- DEPARTMENT
-- ------------------------------------------------------------
CREATE TABLE Department (
    Dept_ID INT PRIMARY KEY,
    Dept_Name VARCHAR(100) NOT NULL,
    Dept_Head VARCHAR(100)
);

INSERT INTO Department (Dept_ID, Dept_Name, Dept_Head)
VALUES (1, 'General Studies', 'System Administrator');

-- ------------------------------------------------------------
-- STUDENT
-- ------------------------------------------------------------
CREATE TABLE Student (
    Student_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT UNIQUE,
    Fname VARCHAR(50) NOT NULL,
    Lname VARCHAR(50) NOT NULL,
    Level VARCHAR(50),
    Birth_Date DATE,
    Student_Email VARCHAR(150),

    -- Composite Address
    City VARCHAR(100),
    Street VARCHAR(150),
    Building_Num VARCHAR(20),

    FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- STUDENT PHONE (Multivalued Attribute) — FR3.2
-- ------------------------------------------------------------
CREATE TABLE Student_Phone (
    Student_ID INT NOT NULL,
    Phone_Num VARCHAR(20) NOT NULL,

    PRIMARY KEY (Student_ID, Phone_Num),

    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- EMPLOYEE
-- ------------------------------------------------------------
CREATE TABLE Employee (
    Emp_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT UNIQUE,
    Emp_FName VARCHAR(50) NOT NULL,
    Emp_Lname VARCHAR(50) NOT NULL,
    Employment_Date DATE,
    Supervisor_ID INT,
    Dept_ID INT NOT NULL,

    FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
        ON DELETE CASCADE,
        
    FOREIGN KEY (Supervisor_ID) REFERENCES Employee(Emp_ID),
    
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID)
);

-- ------------------------------------------------------------
-- EMPLOYEE PHONE (Multivalued Attribute)
-- ------------------------------------------------------------
CREATE TABLE Employee_Phone (
    Emp_ID INT NOT NULL,
    Emp_pnum VARCHAR(20) NOT NULL,
    
    PRIMARY KEY (Emp_ID, Emp_pnum),
    
    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- INSTRUCTOR (Specialization of Employee)
-- ------------------------------------------------------------
CREATE TABLE Instructor (
    Emp_ID INT PRIMARY KEY,
    Qualification VARCHAR(200),

    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- CLASSROOM — FR6.1, FR6.2
-- ------------------------------------------------------------
CREATE TABLE Classroom (
    Classroom_ID INT PRIMARY KEY,
    Classroom_Level VARCHAR(50),
    Classroom_Capacity INT,
    Classroom_Building VARCHAR(100),
    Classroom_Floor VARCHAR(20),
    Is_Lab BOOLEAN DEFAULT FALSE
);

-- ------------------------------------------------------------
-- CLASSROOM EQUIPMENT — FR6.5
-- ------------------------------------------------------------
CREATE TABLE Classroom_Equipment (
    Equipment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Classroom_ID INT NOT NULL,
    Equipment_Name VARCHAR(100) NOT NULL,
    Quantity INT DEFAULT 1,

    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- SUBJECT
-- ------------------------------------------------------------
CREATE TABLE Subject (
    Subject_ID INT PRIMARY KEY,
    Subject_Name VARCHAR(100) NOT NULL,
    Subject_Level VARCHAR(50),
    Subject_Slots INT,
    Classroom_ID INT,

    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID)
);

-- ------------------------------------------------------------
-- STUDIES (Student ↔ Subject) — FR4.2, FR4.3
-- ------------------------------------------------------------
CREATE TABLE Studies (
    Student_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    Grades DECIMAL(5,2),

    PRIMARY KEY (Student_ID, Subject_ID),

    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID)
        ON DELETE CASCADE,
        
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TEACHES (Instructor ↔ Subject)
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

-- ------------------------------------------------------------
-- IS_IN (Student ↔ Classroom) — FR6.3
-- ------------------------------------------------------------
CREATE TABLE Is_In (
    Student_ID INT NOT NULL,
    Classroom_ID INT NOT NULL,

    PRIMARY KEY (Student_ID, Classroom_ID),

    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID)
        ON DELETE CASCADE,

    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID)
        ON DELETE CASCADE
);