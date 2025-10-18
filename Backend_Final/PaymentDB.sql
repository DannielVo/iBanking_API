-- Tạo database
CREATE DATABASE PaymentDB;
GO
USE PaymentDB;
GO

-- Tạo bảng Payment
CREATE TABLE payment (
    transactionId INT IDENTITY(1,1) PRIMARY KEY,
    customerId INT NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    status VARCHAR(10) CHECK (status IN ('unpaid','paid')) NOT NULL,
    transaction_history NVARCHAR(255)
);

-- Dummy data
INSERT INTO payment (customerId, amount, status, transaction_history)
VALUES (101, 900000, 'unpaid', 'Initial unpaid payment for customer 101');

INSERT INTO payment (customerId, amount, status, transaction_history)
VALUES (102, 500000, 'unpaid', 'Initial unpaid payment for customer 102');
