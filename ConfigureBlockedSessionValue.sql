sp_configure 'show advanced options', 1;
GO
RECONFIGURE
GO
sp_configure 'blocked process threshold', 6;
GO
RECONFIGURE ;
GO