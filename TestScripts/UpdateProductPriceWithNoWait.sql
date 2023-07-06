BEGIN TRANSACTION
UPDATE Production.Product
SET StandardCost = 10.00
WHERE Production.Product.ProductID = 1
COMMIT