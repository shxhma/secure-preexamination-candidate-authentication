# Secure Pre-Examination Candidate Authentication System

A face recognition system for securely authenticating exam candidates before entry using AI-powered face detection, liveness (anti-spoof) checking, and automatic report generation.

---

## Requirements

- Python 3.9 or above
- MySQL Server running locally
- A working webcam

---

## Installation

### 1. Install dependencies

Open a terminal in the project folder and run:

```
pip install -r requirements.txt
```

### 2. Download Spoof Detection Models

- Go to the [Silent-Face-Anti-Spoofing GitHub repository](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing)
- Download the `.pth` model files
- Place them inside the `models/` folder in the project directory

### 3. Set up environment variables

Create a `.env` file in the project folder and add your MySQL credentials:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=face_recogniser
```

### 4. Set up the database

```
python setup_db.py
```

This will create the database and the required tables automatically.

### 5. Run the system

```
python main.py
```

---

## Usage

### Exam Registration
Register a candidate by entering their details (name, candidate ID, department, email, phone, etc.) and uploading their photo. The system validates the photo and stores a face embedding in the database.

### Face Recognition
Authenticate a candidate via the live webcam. The system will:
1. Detect the face
2. Ask the candidate to smile (liveness check)
3. Run anti-spoof detection
4. Match the face against the database
5. Grant or deny access based on the result

The candidate has **3 attempts** before being locked out.

### View Reports
View all authentication sessions in a table, filtered by Verified or Declined. You can also:
- Open the **Authenticated Report PDF** — shows all verified candidates with name, ID, phone, email, and time authenticated
- Open the **Declined Report PDF** — shows all declined/locked candidates with timestamp
- **Clear All Logs** — deletes all records from the database and resets both PDFs

### Open Dataset
Opens the `dataset/` folder where registered candidate photos are stored.

---

## Project Structure

```
├── main.py                  # Entry point, main dashboard
├── student.py               # Candidate registration module
├── face_recognition.py      # Live face authentication module
├── reports_viewer.py        # Reports viewer UI
├── photo_validator.py       # Photo upload validation
├── spoof_detection.py       # Anti-spoof logic
├── anti_spoof_predict.py    # Anti-spoof model inference
├── db_config.py             # Database configuration
├── setup_db.py              # Database setup script
├── test_validation.py       # Batch photo validation tester
├── requirements.txt         # Python dependencies
├── .env                     # Your database credentials (not shared)
├── models/                  # Spoof detection .pth model files
├── src/                     # Anti-spoof model source files
├── resources/               # Detection model resources
├── img/                     # UI icons
└── dataset/                 # Registered candidate photos
```

---

## Notes

- The `dataset/` folder contains candidate photos — do not share this publicly.
- The `.env` file contains your database password — keep it private.
- The `venv/` folder (if present) does not need to be shared — each user creates their own.