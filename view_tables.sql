-- Switch to the expense_tracker database
USE expense_tracker;

-- View all tables in the database
SHOW TABLES;

-- View User table data
SELECT * FROM user;

-- View Expense table data
SELECT * FROM expense;

-- View Budget table data
SELECT * FROM budget;

-- View detailed expense data with user information
SELECT 
    e.id,
    e.amount,
    e.category,
    e.description,
    e.date,
    u.username as user
FROM expense e
JOIN user u ON e.user_id = u.id;

-- View detailed budget data with user information
SELECT 
    b.id,
    b.amount,
    b.period,
    b.category,
    u.username as user
FROM budget b
JOIN user u ON b.user_id = u.id;
