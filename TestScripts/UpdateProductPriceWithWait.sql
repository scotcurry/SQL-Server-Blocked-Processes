BEGIN TRANSACTION
UPDATE Production.Product
SET StandardCost = 10.00
WHERE Production.Product.ProductID = 1
WAITFOR DELAY '00:10:00.000'
COMMIT
