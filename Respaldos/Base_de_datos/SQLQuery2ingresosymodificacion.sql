USE EscentopiaDB;
GO

/*ingresar un nuevo registro*/
INSERT INTO Productos (nombre, precio, imagen)
SELECT 'Aroma a especias y naranja', 16.50, BulkColumn
FROM OPENROWSET(BULK 'C:\Users\Usuario\Desktop\Progra-5\Paguina_esentopia\Esentopia_imagenes\aroma6.jpg', SINGLE_BLOB) AS Imagen;

/*actualizar datos de una tabla */

UPDATE Productos
SET nombre = 'Aroma silvestre',
    precio = 7.50,
    imagen = (SELECT BulkColumn 
              FROM OPENROWSET(BULK 'C:\Users\Usuario\Desktop\Progra-5\Paguina_esentopia\Esentopia_imagenes\aroma01.jpg', SINGLE_BLOB) AS Imagen)
WHERE id = 2;