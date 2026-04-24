# University Database (UniversityDB) Schema Documentation

## Overview
This document outlines the database schema for the `UniversityDB` system. It encompasses the structure and relationships for managing departments, staff, students, courses, and facilities within the university.

## Relational Database Concepts Used
To fully understand this schema, it is helpful to be familiar with the following relational database mechanisms used extensively throughout the design:

*   **Primary Key (PK)**: A unique identifier for a row in a table. It guarantees that no two records are identical (e.g., `Emp_ID` in the Employee table).
*   **Foreign Key (FK)**: A link between two tables. It ensures that a value in one table must match an existing primary key broadly in another table, maintaining referential integrity.
*   **ON DELETE / UPDATE CASCADE**: A relational rule indicating that if a parent record is deleted or updated, all associated child records in related tables should be automatically deleted or updated. This is used here to prevent "orphan" records.
*   **ON DELETE SET NULL**: A relational rule where, instead of deleting child records when a parent is deleted, the foreign key reference is blanked out (set to `NULL`). This is used when a relationship ends, but the child entity still needs to exist (e.g., if a Department closes, its Employees aren't automatically deleted).

---

## Detailed Entity Breakdown

### 1. The Core Organization
These tables form the backbone of the university staff and administrative structure.

#### Department
A straightforward configuration table holding department information.
*   **`Dept_ID`** (INT, Primary Key): Unique identifier for the department.
*   **`Dept_Name`** (VARCHAR(255), Not Null): The semantic name of the department.
*   **`Dept_Head`** (VARCHAR(255)): The designated head of the department.

#### Employee
This table represents anyone who works at the university. This table includes two critical foreign key relationships:
*   **`Emp_ID`** (INT, Primary Key): Unique identifier for the employee.
*   **`Emp_Name`**, **`Emp_Lname`** (VARCHAR(255), Not Null): The employee's first and last name.
*   **`Emp_Designation`** (DATE): Employment date or designation date.
*   **`Emp_Pnum`** (VARCHAR(50)): Employee's phone number.
*   **`Dept_ID`** (INT, Foreign Key): Links the employee to the `Department` table. Note the **`ON DELETE SET NULL`** rule here: if a department is deleted, the employees remain in the system, but their department association is wiped blank.
*   **`Supervisor_ID`** (INT, Foreign Key): This links *back to the Employee table itself*. This is known as a **recursive relationship**. It denotes that an employee's supervisor is simply another employee. If a supervisor is deleted, this field becomes `NULL`.

#### Instructor
This table implements an "Inheritance" (or Subtype) pattern. Every instructor is an employee, but not every employee is an instructor.
*   **`Emp_ID`** (INT, Primary Key, Foreign Key): This column serves a dual purpose. It uniquely identifies the Instructor, but importantly, it references the `Employee` table. Due to the **`ON DELETE CASCADE`** rule, if an employee is deleted from the system, their corresponding Instructor record is automatically eliminated. 

#### Instructor_Qualification
Because an instructor can hold multiple degrees (e.g., a Master's and a PhD), a separate table is required to normalize the data. Relational databases do not support arrays/lists natively in a single column without violating normalization rules.
*   **`Emp_ID`** (INT, Foreign Key): References `Instructor`. Cascades on delete.
*   **`Qualification`** (VARCHAR(255)): The specific degree or qualification title.
*   **Primary Key**: This uses a **Composite Key** made of both `Emp_ID` and `Qualification`. This mathematically guarantees that a single instructor cannot be assigned the exact same degree twice.

---

### 2. The Student Body & Academics
These tables store data regarding the student populace and the classes offered.

#### Student
Houses core demographic and academic details for enrolled students.
*   **`Student_ID`** (INT, Primary Key): Unique identifier.
*   **`Level`** (VARCHAR(50)): Academic tier (e.g., Freshman, Graduate).
*   **`Fname`**, **`Lname`** (VARCHAR(255), Not Null): Student's first and last name.
*   **`Birth_Date`** (DATE): Date of birth.
*   **`City`**, **`Street`**, **`Building_Num`**: Physical address information components.

#### Student_Email
Addresses the reality that a student might have multiple email addresses (personal, work, academic). Similar to Instructor qualifications, pulling this into a separate table allows one student to have multiple emails associated with their `Student_ID`.
*   **`Student_ID`** (INT, Foreign Key): References `Student`. Cascades on delete.
*   **`Student_Email`** (VARCHAR(255), Not Null): An email address. 

#### Subject
Maintains the catalog of courses offered by the academic institution.
*   **`Subject_ID`** (VARCHAR(50), Primary Key): Unique course code/identifier (e.g., "CS101").
*   **`Subject_Level`** (VARCHAR(50)): Difficulty or tier of the course.
*   **`Subject_Name`** (VARCHAR(255), Not Null): The conversational title of the course.
*   **`Subject_Status`** (INT): Tracks whether a subject is active or retired.

#### Classroom
Maintains the physical inventory of rooms available for lectures.
*   **`Classroom_ID`** (VARCHAR(50), Primary Key): Unique alphanumeric room identifier.
*   **`Classroom_Level`**, **`Classroom_Floor`**, **`Classroom_Building`**: Locational parameters.
*   **`Classroom_Capacity`** (INT): The maximum permitted enrollment for the room.

---

### 3. The Relationship Connectors (Junction Tables)
To resolve "Many-to-Many" associations (e.g., a student takes many subjects, and a subject has many students), the database utilizes junction tables (also known as linking or intersection tables). 

#### Is_In (Classroom to Subject Mapping)
A single subject might have lectures in multiple rooms, and a single room might host multiple different subjects throughout a week. This table mediates that relationship.
*   **Foreign Keys**: `Classroom_ID` and `Subject_ID`. 
*   **Behavior**: They form a composite primary key. If either the specific classroom or the specific subject is deleted from the system, this scheduling link is automatically destroyed (CASCADE).

#### Teaches (Instructor to Subject Mapping)
An instructor can teach multiple subjects, while a large subject might require multiple instructors to handle all sections.
*   **Foreign Keys**: `Emp_ID` (referencing `Instructor`) and `Subject_ID`.
*   **Behavior**: Handled as a composite primary key with CASCADE deletion rules.

#### Studies (Student to Subject Mapping)
This tracks student enrollments. 
*   **Foreign Keys**: `Student_ID` and `Subject_ID`. 
*   **Payload Data (`Grade`)**: Importantly, this junction table carries an extra piece of data: `Grade` (VARCHAR(10)). This architectural choice is deliberate because a grade only logically exists within the context of a specific student analyzing a specific subject.

---
