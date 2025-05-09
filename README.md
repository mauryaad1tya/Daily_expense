# Daily Expense Tracker

A simple web application to track daily expenses using Flask and MySQL.

## Features

- User authentication (register/login)
- Add, view expenses
- Categorize expenses
- View total expenses
- Responsive design

## Setup Instructions

1. Create a MySQL database:
```sql
CREATE DATABASE expense_tracker;
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the environment:
   - Copy `.env.example` to `.env`
   - Update the MySQL connection details in `.env`
   - Change the SECRET_KEY in `.env`

4. Run the application:
```bash
python app.py
```

5. Access the application at: http://localhost:5000

## Database Structure

The application uses two main tables:
- Users: Stores user authentication information
- Expenses: Stores expense records with category, amount, and description

## Technologies Used

- Python Flask
- MySQL
- SQLAlchemy
- Flask-Login for authentication
- Bootstrap 5 for UI
"# Daily_expense" 
