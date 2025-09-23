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
    username NVARCHAR(100) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL
);
GO

INSERT INTO authentication (username, password_hash)
VALUES 
('user1', '$2b$12$S4FIC9fmS5Mg2BEA5hjIGOLIlI1WBQhg.sOU6Ht0G9xH2eHsbgVAe'),
('user2', '$2b$12$vwLOSggSsGjAoV3gic2fIuGcyDf.q1d8nhd0a4nM6AFG286Ba.COW');
GO