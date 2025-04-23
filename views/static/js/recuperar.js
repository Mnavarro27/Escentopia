document.addEventListener("DOMContentLoaded", () => {
  const metodoSelect = document.getElementById("metodoRecuperacion")
  const recuperarPorCorreoDiv = document.getElementById("recuperarPorCorreo")
  const recuperarPorPreguntasDiv = document.getElementById("recuperarPorPreguntas")
  const mensajeEl = document.getElementById("mensaje")
  const codigoDiv = document.getElementById("codigoDiv")
  const enviarBtn = document.getElementById("enviar-codigo")
  const verificarCodigoBtn = document.getElementById("verificar-codigo")
  const verificarPreguntaBtn = document.getElementById("verificar-pregunta")
  const successEmailEl = document.getElementById("success-email")
  const successPreguntaEl = document.getElementById("success-pregunta")

  // Animaciones para los botones
  const buttons = document.querySelectorAll("button")
  buttons.forEach((button) => {
    button.addEventListener("mousedown", function () {
      this.style.transform = "scale(0.98)"
    })

    button.addEventListener("mouseup", function () {
      this.style.transform = "scale(1)"
    })
  })

  // Cambiar la visibilidad de los métodos de recuperación
  metodoSelect.addEventListener("change", () => {
    const opcion = metodoSelect.value
    recuperarPorCorreoDiv.style.display = opcion === "email" ? "block" : "none"
    recuperarPorPreguntasDiv.style.display = opcion === "preguntas" ? "block" : "none"
    mensajeEl.style.display = "none" // Limpiar mensajes previos

    // Resetear los formularios
    if (opcion === "email") {
      document.getElementById("username-email").focus()
    } else if (opcion === "preguntas") {
      document.getElementById("username").focus()
    }
  })

  // Validación de entrada para el código (solo números)
  const codigoInput = document.getElementById("codigo")
  if (codigoInput) {
    codigoInput.addEventListener("input", function (e) {
      this.value = this.value.replace(/[^0-9]/g, "")
    })
  }

  // Enviar código al correo
  if (enviarBtn) {
    enviarBtn.addEventListener("click", async () => {
      const username = document.getElementById("username-email").value.trim()
      const email = document.getElementById("email").value.trim()

      if (!username || !email) {
        mostrarMensaje("Por favor, completa todos los campos.")
        return
      }

      // Validar formato de correo electrónico
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email)) {
        mostrarMensaje("Por favor, ingresa un correo electrónico válido.")
        return
      }

      // Mostrar estado de carga
      enviarBtn.disabled = true
      enviarBtn.textContent = "Enviando..."
      enviarBtn.style.backgroundColor = "#999"

      try {
        // Primero intentamos con la ruta API
        let response = await fetch("/api/recuperacion/enviar-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, email }),
        })

        if (!response.ok) {
          // Si falla, intentamos con la ruta directa
          response = await fetch("/recuperacion/enviar-token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email }),
          })
        }

        const data = await response.json()

        if (response.ok) {
          // Mostrar mensaje de éxito
          successEmailEl.textContent = "Se ha enviado un código a tu correo. Ingrésalo para continuar."
          successEmailEl.style.display = "block"

          // Guardar el username para la verificación
          localStorage.setItem("recovery_username", username)

          // Mostrar el div del código
          codigoDiv.style.display = "block"

          // Enfocar el campo de código
          document.getElementById("codigo").focus()
        } else {
          mostrarMensaje(data.error || "Error al enviar el código.")
        }
      } catch (error) {
        console.error("Error en el envío de código:", error)
        mostrarMensaje("Error de conexión con el servidor.")
      } finally {
        // Restaurar el botón
        enviarBtn.disabled = false
        enviarBtn.textContent = "Enviar Código"
        enviarBtn.style.backgroundColor = ""
      }
    })
  }

  // Verificar el código antes de cambiar la contraseña
  if (verificarCodigoBtn) {
    verificarCodigoBtn.addEventListener("click", async () => {
      const username = localStorage.getItem("recovery_username")
      const codigo = document.getElementById("codigo").value.trim()

      if (!username) {
        mostrarMensaje("Error: No se encontró el nombre de usuario. Intenta nuevamente.")
        return
      }

      if (!codigo) {
        mostrarMensaje("Por favor, ingresa el código recibido.")
        return
      }

      if (codigo.length !== 6) {
        mostrarMensaje("El código debe tener 6 dígitos.")
        return
      }

      // Mostrar estado de carga
      verificarCodigoBtn.disabled = true
      verificarCodigoBtn.textContent = "Verificando..."
      verificarCodigoBtn.style.backgroundColor = "#999"

      try {
        // Primero intentamos con la ruta API
        let response = await fetch("/api/recuperacion/verificar-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, codigo }),
        })

        if (!response.ok) {
          // Si falla, intentamos con la ruta directa
          response = await fetch("/recuperacion/verificar-token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, codigo }),
          })
        }

        const data = await response.json()

        if (response.ok && data.success) {
          // Mostrar mensaje de éxito
          successEmailEl.textContent = "Código verificado correctamente. Redirigiendo..."
          successEmailEl.style.display = "block"

          // Esperar un momento para mostrar el mensaje
          setTimeout(() => {
            window.location.href = `cambiar-contrasena.html?username=${encodeURIComponent(username)}`
          }, 1500)
        } else {
          mostrarMensaje(data.error || "Código incorrecto.")

          // Restaurar el botón
          verificarCodigoBtn.disabled = false
          verificarCodigoBtn.textContent = "Verificar Código"
          verificarCodigoBtn.style.backgroundColor = ""
        }
      } catch (error) {
        console.error("Error al verificar código:", error)
        mostrarMensaje("Error de conexión con el servidor.")

        // Restaurar el botón
        verificarCodigoBtn.disabled = false
        verificarCodigoBtn.textContent = "Verificar Código"
        verificarCodigoBtn.style.backgroundColor = ""
      }
    })
  }

  // Función para mostrar mensajes de error con animación
  function mostrarMensaje(msg) {
    mensajeEl.textContent = msg
    mensajeEl.style.display = "block"

    // Aplicar animación de shake
    mensajeEl.style.animation = "none"
    setTimeout(() => {
      mensajeEl.style.animation = "shake 0.5s ease-in-out"
    }, 10)
  }
})
