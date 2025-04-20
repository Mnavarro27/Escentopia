CREATE DATABASE EscentopiaDB;
GO

USE EscentopiaDB;
GO

CREATE TABLE Productos (
    id INT IDENTITY(1,1) PRIMARY KEY, -- ID autoincremental
    nombre NVARCHAR(255) NOT NULL, -- Nombre del producto
    precio DECIMAL(10,2) NOT NULL, -- Precio del producto
    imagen VARBINARY(MAX) -- URL de la imagen del producto
);
GO


USE EscentopiaDB;
GO

-- Crear la tabla Usuarios
CREATE TABLE Usuarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    apellido NVARCHAR(100) NOT NULL,
    tipo_identificacion NVARCHAR(50) NOT NULL,
    identificacion NVARCHAR(50) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    sexo NVARCHAR(50) NOT NULL,
    direccion NVARCHAR(255) NOT NULL,
    telefono NVARCHAR(50) NOT NULL,
    correo NVARCHAR(100) NOT NULL,
    username NVARCHAR(50) NOT NULL UNIQUE,
    password NVARCHAR(50) NOT NULL,
    nombre_tarjeta NVARCHAR(100) NOT NULL,
    numero_tarjeta NVARCHAR(50) NOT NULL,
    fecha_vencimiento NVARCHAR(10) NOT NULL,  -- Se puede almacenar como 'MM-YYYY'
    codigo_seguridad NVARCHAR(3) NOT NULL       -- Código de 3 dígitos
);

INSERT INTO Productos (nombre, precio, imagen)
SELECT 'Aroma de Lavanda Relajante', 10.50, BulkColumn
FROM OPENROWSET(BULK 'C:\Users\Usuario\Desktop\Progra-5\Paguina_esentopia\Esentopia_imagenes\aroma0.jpg', SINGLE_BLOB) AS Imagen;

INSERT INTO Productos (nombre, precio, imagen)
SELECT 'Aroma silvestre', 8.50, BulkColumn
FROM OPENROWSET(BULK 'C:\Users\Usuario\Desktop\Progra-5\Paguina_esentopia\Esentopia_imagenes\aroma01.jpg', SINGLE_BLOB) AS Imagen;

INSERT INTO usuario (nombre, passwords, imagen)
SELECT 'Mauricio','mau', BulkColumn
FROM OPENROWSET(BULK 'C:\Users\Usuario\Desktop\Progra-5\Paguina_esentopia\Esentopia_imagenes\aroma0.jpg', SINGLE_BLOB) AS Imagen;


SELECT @@SERVERNAME AS NombreServidor, SERVERPROPERTY('InstanceName') AS NombreInstancia;


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

USE EscentopiaDB;
GO


ALTER TABLE Usuarios
ADD show_onboarding BIT NOT NULL
    CONSTRAINT DF_Usuarios_ShowOnboarding DEFAULT 1;

	ALTER TABLE Usuarios 
  ALTER COLUMN fecha_vencimiento DATE NULL;