USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'AccountDB')
BEGIN
    ALTER DATABASE AccountDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE AccountDB;
END;


CREATE DATABASE AccountDB;
GO

USE AccountDB;
GO
CREATE TABLE account (
    account_id NVARCHAR(50) PRIMARY KEY,
    customer_id NVARCHAR(50),
    balance DECIMAL(18,2) DEFAULT 0
);

-- Thêm dữ liệu mẫu
INSERT INTO account (account_id, customer_id, balance)
VALUES 
    ('ACC001', '101', 1000000.50),
    ('ACC002', '102', 250000.00),
    ('ACC003', '103', 50000.75),   -- cùng 1 customer có nhiều account
    ('ACC004', '101', 0.00),
    ('ACC005', '104', 99999999.99),
	('ACC006', '105', 99999999.99),
	('ACC007', '105', 99999999.99);
go
select * from account 