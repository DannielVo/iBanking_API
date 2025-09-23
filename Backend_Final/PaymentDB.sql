create database PaymentDB

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'PaymentDB')
BEGIN
    CREATE DATABASE PaymentDB;
END
GO

USE PaymentDB;
GO

-- Xóa bảng cũ nếu có
IF OBJECT_ID('dbo.payment', 'U') IS NOT NULL
    DROP TABLE dbo.payment;
GO

-- Bảng payment
CREATE TABLE payment (
    transactionId INT IDENTITY(1,1) PRIMARY KEY,
    accountId INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status NVARCHAR(50) DEFAULT 'PENDING',
    transaction_history NVARCHAR(MAX) NULL
);
GO