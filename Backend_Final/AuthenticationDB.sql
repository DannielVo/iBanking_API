create database AuthenticationDB

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'AuthenticationDB')
BEGIN
    CREATE DATABASE AuthenticationDB;
END
GO

USE AuthenticationDB;
GO

-- Xóa bảng cũ nếu có
IF OBJECT_ID('dbo.authentication', 'U') IS NOT NULL
    DROP TABLE dbo.authentication;
GO

-- Bảng authentication
CREATE TABLE authentication (
    userId INT IDENTITY(1,1) PRIMARY KEY,
    customer_id NVARCHAR(50),
    username NVARCHAR(100) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL
);
GO

INSERT INTO authentication (username, customer_id, password_hash)
VALUES 
('a@example.com', '101', '$2b$12$wwN5O.TbLDNeYYR3pHZfWusdUCwcXLZTzXK4P2F15p5DG3LY1KxhW'),
('b@example.com', '102', '$2b$12$wwN5O.TbLDNeYYR3pHZfWusdUCwcXLZTzXK4P2F15p5DG3LY1KxhW');
GO