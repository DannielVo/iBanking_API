create database OtpDB

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'OtpDB')
BEGIN
    CREATE DATABASE OtpDB;
END
GO

USE OtpDB;
GO

-- Xóa bảng cũ nếu có
IF OBJECT_ID('dbo.otp', 'U') IS NOT NULL
    DROP TABLE dbo.otp;
GO

-- Bảng otp
CREATE TABLE otp (
    otpId INT IDENTITY(1,1) PRIMARY KEY,
    userId INT NOT NULL,
    otpCode NVARCHAR(10) NOT NULL,
    expired_at DATETIME NOT NULL,
    is_used BIT DEFAULT 0
);
GO