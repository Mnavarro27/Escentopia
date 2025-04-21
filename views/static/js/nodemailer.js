const nodemailer = require("nodemailer");

// Configuración SMTP (ajusta estos valores según tu proveedor)
const transporter = nodemailer.createTransport({
  host: "smtp.gmail.com", // Cambia por el host de tu proveedor
  port: 587, // Cambia por el puerto correcto, por ejemplo, 587 o 465
  secure: false, // Usa true para 465, false para 587
  auth: {
    user: "mau4189@gmail.com", // Tu correo
    pass: "27SmanS17*" // Tu contraseña
  }
});


// Verificar la conexión
transporter.verify(function (error, success) {
  if (error) {
    console.error("Error al conectar con el servidor SMTP:", error);
  } else {
    console.log("El servidor SMTP está listo para enviar correos.");
  }
});
