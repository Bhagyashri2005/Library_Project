# 📚 Smart Library Access System

## 🔹 Project Description
The Smart Library Access System is a full-stack web application designed to automate library entry and exit using barcode-based scanning. It replaces manual registers and provides real-time monitoring, member management, and administrative control through a centralized dashboard.

---

## 🔹 Key Features
- Barcode-based Entry & Exit System
- Real-time Logs Tracking
- Manual Entry Support
- Member Management
- Timetable Management
- Admin Dashboard
- Secure Backend APIs

---

## 🔹 Technology Stack

### Frontend
- React.js
- CSS
- Axios

### Backend
- FastAPI (Python)

### Database
- MySQL

---

## 🔹 System Architecture
Barcode Scanner → React Frontend → FastAPI Backend → MySQL Database

---

## 🔹 Installation & Setup

### Frontend and Backend Setup
```bash
# Frontend (React)
npm install
npm run dev

# Backend (FastAPI)
pip install -r requirements.txt
uvicorn main:app --reload

```
---

## 🔹 Database Structure (MySQL)

```sql
-- Academic Calendar Table
CREATE TABLE academic_calendar (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    event_type VARCHAR(50),
    description VARCHAR(255)
);

-- Students Table
CREATE TABLE students (
    student_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    year VARCHAR(10),
    division VARCHAR(10),
    email VARCHAR(100),
    contact_no VARCHAR(15),
    batch VARCHAR(5) NOT NULL
);

-- Teachers Table
CREATE TABLE teachers (
    teacher_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    email VARCHAR(100),
    contact_no VARCHAR(15),
    designation VARCHAR(50)
);

-- Logs Table
CREATE TABLE logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    scan_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action ENUM('ENTRY','EXIT') NOT NULL,
    status ENUM('NORMAL','SKIP') DEFAULT 'NORMAL',
    matched_subject VARCHAR(100),
    matched_teacher_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Timetable Table
CREATE TABLE timetable (
    timetable_id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(50) NOT NULL,
    year ENUM('FE','SE','TE','BE') NOT NULL,
    division VARCHAR(5) NOT NULL,
    batch VARCHAR(5),
    subject VARCHAR(100) NOT NULL,
    teacher_id VARCHAR(10) NOT NULL,
    day_of_week ENUM(
        'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'
    ) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    type ENUM('Lecture','Practical') NOT NULL
);

-- Admin Table
CREATE TABLE admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
```