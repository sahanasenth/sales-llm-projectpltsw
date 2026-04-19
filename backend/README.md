# Sales LLM Project - Backend

A backend service built with Django and Django REST Framework for managing sales processes including customer inquiries, appointments, and feedback. It uses PostgreSQL as the database.

## Prerequisites

- Python 3.10+
- PostgreSQL
- Git

## Setup Instructions

Follow these steps to set up the project on your local machine.

### 1. Clone the repository

```bash
git clone https://github.com/sahanasenth/sales-llm-projectpltsw.git
cd sales-llm-projectpltsw/backend
```
*(Note: Ensure you always `cd` into the `backend` directory before running any backend commands!)*

### 2. Set up a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

### 4. Database Setup

Make sure you have PostgreSQL running and create a database for this project.

1. Create a `.env` file in the `backend/` directory.
2. Update the `DATABASES` configuration inside `sales_project/settings.py` or `.env` to match your local PostgreSQL credentials (user, password, host, port, database name).

### 5. Apply Migrations

Run Django migrations to create the database schema:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

To access the Django Admin panel, create a superuser:

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

Start the local server:

```bash
python manage.py runserver
```

The application will be running at `http://127.0.0.1:8000/`.
