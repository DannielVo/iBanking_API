CREATE DATABASE EmailDB
GO
USE EmailDB
GO
CREATE TABLE EmailLogs (
    id INT IDENTITY PRIMARY KEY,
    recipient NVARCHAR(255) NOT NULL,
    subject NVARCHAR(255),
    status NVARCHAR(20),             -- success | failed
    error_message NVARCHAR(500) NULL,
    sent_time DATETIME DEFAULT GETDATE()
);
