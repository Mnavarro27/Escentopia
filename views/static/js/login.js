document.addEventListener("DOMContentLoaded", () => {
    localStorage.removeItem("usuario"); // limpiamos cualquier sesión previa
  
    const loginButton = document.getElementById("login-button");
    const errorMessage = document.getElementById("error-message");
    const bloqueoMensaje = document.getElementById("bloqueo-mensaje");
  
    loginButton.addEventListener("click", async (e) => {
      e.preventDefault();
  
      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value.trim();
  
      if (!username || !password) {
        errorMessage.textContent = "Por favor, ingresa un usuario y contraseña.";
        errorMessage.style.display = "block";
        return;
      }
  
      try {
        const response = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password })
        });
  
        const data = await response.json();
  
        if (response.ok) {
          console.log("Usuario recibido del servidor:", data.usuario);
          // Guardamos temporalmente al usuario hasta completar 2FA
          localStorage.setItem("usuario_temp", JSON.stringify(data.usuario));
          // Enviamos el código 2FA
          await solicitarCodigo2FA(username);
  
        } else {
          // manejo de bloqueos e intents
          if (data.bloqueado_hasta) {
            mostrarTiempoBloqueo(data.bloqueado_hasta);
          } else {
            errorMessage.textContent = data.error || "Usuario o contraseña incorrectos.";
            errorMessage.style.display = "block";
          }
        }
  
      } catch (error) {
        console.error("Error de conexión con el servidor:", error);
        errorMessage.textContent = "Error de conexión con el servidor.";
        errorMessage.style.display = "block";
      }
    });
  
    // Envío del 2FA
// Función para solicitar código 2FA
async function solicitarCodigo2FA(username) {
  try {
    const response = await fetch("/api/autenticacion/solicitar-2fa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    })

    const data = await response.json()

    if (response.ok) {
      return { success: true }
    } else {
      return { success: false, error: data.error || "Error al solicitar código 2FA" }
    }
  } catch (error) {
    console.error("Error solicitando 2FA:", error)
    return { success: false, error: "Error de conexión con el servidor" }
  }
}

  
    // Mostrar tiempo de bloqueo
    function mostrarTiempoBloqueo(bloqueadoHasta) {
      const desbloqueoTime = new Date(bloqueadoHasta).getTime();
      function actualizarTiempo() {
        const ahora = Date.now();
        const tiempoRestante = desbloqueoTime - ahora;
        if (tiempoRestante > 0) {
          const minutos = Math.floor(tiempoRestante / 60000);
          const segundos = Math.floor((tiempoRestante % 60000) / 1000);
          bloqueoMensaje.textContent =
            `Cuenta bloqueada. Intenta nuevamente en ${minutos}m ${segundos}s.`;
          bloqueoMensaje.style.display = "block";
          setTimeout(actualizarTiempo, 1000);
        } else {
          bloqueoMensaje.style.display = "none";
        }
      }
      actualizarTiempo();
    }
  });
  
  
  // Mostrar/ocultar contraseña
  function togglePassword() {
    const passwordInput = document.getElementById("password");
    passwordInput.type =
      passwordInput.type === "password" ? "text" : "password";
  }
  // Hago togglePassword global
  window.togglePassword = togglePassword;
  