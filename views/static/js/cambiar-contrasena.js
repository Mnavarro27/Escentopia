document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const email = urlParams.get("email");
  const username = urlParams.get("username");
  const identificadorInput = document.getElementById("identificador");

  // Determinar si el usuario llegó por correo o por preguntas de seguridad
  let identificador;
  if (email) {
    identificador = email;
    identificadorInput.value = email;
  } else if (username) {
    identificador = username;
    identificadorInput.value = username;
  } else {
    alert("Error: No se proporcionó un identificador válido.");
    window.location.href = "recuperar.html";
    return;
  }

  const passwordInput = document.getElementById("password");
  const confirmPasswordInput = document.getElementById("confirmPassword");
  const mensajeEl = document.getElementById("mensaje");

  // 📌 Validaciones en tiempo real de la contraseña
  const lengthCheck = document.getElementById("length");
  const uppercaseCheck = document.getElementById("uppercase");
  const lowercaseCheck = document.getElementById("lowercase");
  const numberCheck = document.getElementById("number");
  const specialCheck = document.getElementById("special");

  passwordInput.addEventListener("input", function () {
    const password = passwordInput.value;

    // Expresiones regulares para validar cada criterio
    const lengthValid = password.length >= 8;
    const uppercaseValid = /[A-Z]/.test(password);
    const lowercaseValid = /[a-z]/.test(password);
    const numberValid = /\d/.test(password);
    const specialValid = /[@$!%*?&]/.test(password);

    updateValidationStatus(lengthCheck, lengthValid);
    updateValidationStatus(uppercaseCheck, uppercaseValid);
    updateValidationStatus(lowercaseCheck, lowercaseValid);
    updateValidationStatus(numberCheck, numberValid);
    updateValidationStatus(specialCheck, specialValid);
  });

  function updateValidationStatus(element, isValid) {
    if (isValid) {
      element.classList.remove("invalid");
      element.classList.add("valid");
      element.innerHTML = element.innerHTML.replace("❌", "✅");
    } else {
      element.classList.remove("valid");
      element.classList.add("invalid");
      element.innerHTML = element.innerHTML.replace("✅", "❌");
    }
  }

  // 📌 Manejar el envío de la nueva contraseña
  document.getElementById("cambiar-contrasena").addEventListener("click", async () => {
    const password = passwordInput.value.trim();
    const confirmPassword = confirmPasswordInput.value.trim();

    if (!password || !confirmPassword) {
      mensajeEl.textContent = "Por favor, completa todos los campos.";
      mensajeEl.style.display = "block";
      return;
    }

    // Validar que las contraseñas coincidan
    if (password !== confirmPassword) {
      mensajeEl.textContent = "Las contraseñas no coinciden.";
      mensajeEl.style.display = "block";
      return;
    }

    // Validar que la contraseña cumpla con los requisitos
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    if (!passwordPattern.test(password)) {
      mensajeEl.textContent = "La contraseña no cumple con los requisitos.";
      mensajeEl.style.display = "block";
      return;
    }

    try {
      const response = await fetch("/api/recuperacion/cambiar-contrasena", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identificador, nuevaPassword: password })
    });
      const text = await response.text(); // Leer como texto primero

      // Intentar parsear JSON manualmente
      let data;
      try {
        data = JSON.parse(text);
      } catch (jsonError) {
        throw new Error("Respuesta del servidor no válida. No es un JSON.");
      }

      if (!response.ok) {
        throw new Error(data.error || "Error al actualizar la contraseña.");
      }

      alert("Contraseña actualizada correctamente.");
      window.location.href = "login.html";
    } catch (error) {
      console.error("Error de conexión:", error);
      mensajeEl.textContent = error.message || "Error de conexión con el servidor.";
      mensajeEl.style.display = "block";
    }

  });
});

/* Función para mostrar/ocultar la contraseña
function togglePassword() {
  const passwordInput = document.getElementById("password");
  if (passwordInput.type === "password") {
    passwordInput.type = "text";
  } else {
    passwordInput.type = "password";
  }
}
*/
// Función para mostrar/ocultar la contraseña
function togglePassword(inputId) {
  const pwd = document.getElementById(inputId);
  pwd.type = pwd.type === "password" ? "text" : "password";
}
