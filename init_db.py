from app import app, db, User, Expense, Budget
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    # Drop existing tables
    db.drop_all()

    # Create tables
    db.create_all()

    print('Creating test user...')
    # Create a test user
    test_user = User(
        username='test',
        email='test@example.com'
    )
    test_user.set_password('test123')
    db.session.add(test_user)

    print('Creating sample expenses...')
    # Create some sample expenses
    sample_expenses = [
        Expense(
            amount=500.00,
            category='Food',
            description='Grocery shopping',
            date=datetime.now(),
            user=test_user
        ),
        Expense(
            amount=1000.00,
            category='Bills',
            description='Electricity bill',
            date=datetime.now(),
            user=test_user
        )
    ]

    for expense in sample_expenses:
        db.session.add(expense)

    print('Creating sample budgets...')
    # Create sample budgets
    sample_budgets = [
        Budget(
            amount=5000.00,
            period='monthly',
            category='Food',
            user=test_user
        ),
        Budget(
            amount=10000.00,
            period='monthly',
            user=test_user
        )
    ]

    for budget in sample_budgets:
        db.session.add(budget)

    # Commit changes
    db.session.commit()

    print('Database initialized with sample data!')
