document.addEventListener("DOMContentLoaded", () => {
  // Elementos del DOM
  const codigoInput = document.getElementById("codigo-2fa")
  const verificarBtn = document.getElementById("verificar-2fa-button")
  const mensajeError = document.getElementById("mensaje-error")
  const mensajeExito = document.getElementById("mensaje-exito")

  // Obtener el username de la URL
  const urlParams = new URLSearchParams(window.location.search)
  const username = urlParams.get("username")

  if (!username) {
    mostrarError("Error: No se proporcionó un nombre de usuario válido.")
    verificarBtn.disabled = true
    return
  }

  // Enfocar automáticamente el campo de entrada
  codigoInput.focus()

  // Formatear automáticamente el código mientras se escribe
  codigoInput.addEventListener("input", function () {
    // Permitir solo números
    this.value = this.value.replace(/[^0-9]/g, "")

    // Ocultar mensaje de error cuando el usuario comienza a escribir de nuevo
    mensajeError.style.display = "none"
  })

  // Manejar la verificación del código
  verificarBtn.addEventListener("click", verificarCodigo)

  // También permitir enviar con Enter
  codigoInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      verificarCodigo()
    }
  })

  function verificarCodigo() {
    const codigo = codigoInput.value.trim()

    if (codigo.length !== 6) {
      mostrarError("Por favor, ingresa el código completo de 6 dígitos.")
      return
    }
    

    // Mostrar estado de carga
    const textoOriginal = verificarBtn.textContent
    verificarBtn.innerHTML = '<span class="loading"></span> Verificando...'
    verificarBtn.disabled = true

    // Enviar solicitud al servidor
    fetch("/verificar-2fa", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username,
        codigo2FA: codigo,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Mostrar mensaje de éxito
          mensajeExito.style.display = "block"

          // Guardar en localStorage que el usuario está verificado
          const usuario = JSON.parse(localStorage.getItem("usuario") || "{}")
          usuario.verificado = true
          localStorage.setItem("usuario", JSON.stringify(usuario))

          // Redirigir después de un breve retraso
          setTimeout(() => {
            window.location.href = "/index.html"
          }, 2000)
        } else {
          // Restaurar el botón
          verificarBtn.innerHTML = textoOriginal
          verificarBtn.disabled = false

          // Mostrar error
          mostrarError(data.error || "Código incorrecto. Por favor, intenta de nuevo.")

          // Limpiar y enfocar el campo
          codigoInput.value = ""
          codigoInput.focus()
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        verificarBtn.innerHTML = textoOriginal
        verificarBtn.disabled = false
        mostrarError("Error de conexión. Por favor, intenta de nuevo.")
      })
  }

  function mostrarError(mensaje) {
    mensajeError.textContent = mensaje
    mensajeError.style.display = "block"

    // Aplicar animación de shake
    mensajeError.style.animation = "none"
    setTimeout(() => {
      mensajeError.style.animation = "shake 0.5s ease-in-out"
    }, 10)
  }
})
