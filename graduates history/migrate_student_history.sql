-- ============================================================
--  Migration: Student Status / Graduate History Feature
--  Run this against your existing school_db database
-- ============================================================

USE school_db;

-- Add Status column (defaults to 'ongoing' for all existing students)
ALTER TABLE Student 
ADD COLUMN Status ENUM('ongoing', 'gap_year', 'expelled', 'graduated') 
    NOT NULL DEFAULT 'ongoing'
AFTER Level;

-- Add Graduation_Date for historical record-keeping
ALTER TABLE Student
ADD COLUMN Graduation_Date DATE NULL
AFTER Status;

-- Add Status_Notes for context (reason for expulsion, gap year plans, etc.)
ALTER TABLE Student
ADD COLUMN Status_Notes VARCHAR(255) NULL
AFTER Graduation_Date;

-- Verify the changes
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'school_db' 
  AND TABLE_NAME = 'Student'
  AND COLUMN_NAME IN ('Status', 'Graduation_Date', 'Status_Notes');
