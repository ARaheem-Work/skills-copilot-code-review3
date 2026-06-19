# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements from the database
- Manage announcements (create, edit, delete) when signed in as a teacher/admin

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements/active`                                           | Get all currently active announcements for public display           |
| GET    | `/announcements?teacher_username={username}`                      | Get all announcements for management (requires sign-in)             |
| POST   | `/announcements?...`                                              | Create announcement (requires sign-in)                              |
| PUT    | `/announcements/{announcement_id}?...`                            | Update announcement (requires sign-in)                              |
| DELETE | `/announcements/{announcement_id}?teacher_username={username}`    | Delete announcement (requires sign-in)                              |

Announcement create/update parameters:

- `message` (required)
- `expiration_date` (required, `YYYY-MM-DD`)
- `start_date` (optional, `YYYY-MM-DD`)
- `teacher_username` (required for management endpoints)

## Data Model

The application uses MongoDB with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Teachers** - Uses username as identifier:
   - Display name
   - Argon2 password hash
   - Role

3. **Announcements** - Uses MongoDB ObjectId as identifier:
   - Message
   - Optional start date
   - Required expiration date
   - Created by
   - Created timestamp

Data is loaded from MongoDB, and sample records are initialized in `backend/database.py` when collections are empty.
