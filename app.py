from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:password@localhost/expense_tracker')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S')
        }

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)  # 'weekly' or 'monthly'
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50))  # Optional category-specific budget
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def get_remaining(self):
        end_date = self.get_period_end()
        expenses = Expense.query.filter(
            Expense.user_id == self.user_id,
            Expense.date >= self.start_date,
            Expense.date <= end_date
        )
        if self.category:
            expenses = expenses.filter(Expense.category == self.category)
        
        total_spent = sum(e.amount for e in expenses)
        return self.amount - total_spent

    def get_period_end(self):
        if self.period == 'weekly':
            return self.start_date + timedelta(days=7)
        return self.start_date + timedelta(days=30)  # monthly

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    # Get filter parameters
    category = request.args.get('category')
    period = request.args.get('period', 'all')  # all, day, week, month
    
    # Base query
    query = Expense.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if category:
        query = query.filter_by(category=category)
    
    if period != 'all':
        today = datetime.now()
        if period == 'day':
            query = query.filter(Expense.date >= today.replace(hour=0, minute=0, second=0))
        elif period == 'week':
            week_ago = today - timedelta(days=7)
            query = query.filter(Expense.date >= week_ago)
        elif period == 'month':
            month_ago = today - timedelta(days=30)
            query = query.filter(Expense.date >= month_ago)
    
    expenses = query.order_by(Expense.date.desc()).all()
    total = sum(expense.amount for expense in expenses)
    
    # Get budget information
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    budget_info = [{
        'period': budget.period,
        'amount': budget.amount,
        'remaining': budget.get_remaining(),
        'category': budget.category or 'All Categories'
    } for budget in budgets]
    
    # Get unique categories for filter
    categories = db.session.query(Expense.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('index.html', 
                           expenses=expenses, 
                           total=total,
                           categories=categories,
                           current_category=category,
                           current_period=period,
                           budgets=budget_info)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form.get('description', '')
        date_str = request.form.get('date')
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date = datetime.now()
        
        expense = Expense(amount=amount, category=category, description=description,
                         date=date, user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_expense.html')

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        expense.amount = float(request.form['amount'])
        expense.category = request.form['category']
        expense.description = request.form.get('description', '')
        date_str = request.form.get('date')
        if date_str:
            expense.date = datetime.strptime(date_str, '%Y-%m-%d')
        
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_expense.html', expense=expense)

@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        abort(403)
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def manage_budget():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        period = request.form['period']
        category = request.form.get('category')
        
        # Check for existing budget in the same category
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            period=period,
            category=category
        ).first()
        
        if existing_budget:
            existing_budget.amount = amount
            existing_budget.start_date = datetime.now()
        else:
            budget = Budget(amount=amount, period=period, category=category,
                           user_id=current_user.id)
            db.session.add(budget)
        
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('index'))
    
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    categories = db.session.query(Expense.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('budget.html', budgets=budgets, categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
