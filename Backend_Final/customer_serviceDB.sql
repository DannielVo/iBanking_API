USE master;
GO
-- Đóng tất cả kết nối tới CustomerDB
ALTER DATABASE CustomerDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
go

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'CustomerDB')
BEGIN
    DROP DATABASE CustomerDB;
END

CREATE DATABASE CustomerDB;
GO

USE CustomerDB;
GO

CREATE TABLE Customers (
    customer_id NVARCHAR(50) PRIMARY KEY,
    full_name NVARCHAR(100) NOT NULL,
    phone_number NVARCHAR(15) NOT NULL,
    email NVARCHAR(100) NOT NULL 
);
go	
INSERT INTO Customers (customer_id, full_name, phone_number, email)
VALUES 
('101', N'Nguyen Van A', '0909123456', 'a@example.com'),
('102', N'Nguyen Van B', '0912345678', 'b@example.com'),
('103', N'Nguyen Hong Phu', '0923456789', 'p@example.com'),
('104', N'Tran Thi C', '0934567890', 'c@example.com'),
('105', N'Le Van D', '0945678901', 'd@example.com');

select * from Customers