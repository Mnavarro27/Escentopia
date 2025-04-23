// static/js/registro.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registro-form")
  const passwordInput = document.getElementById("password")
  const passwordError = document.getElementById("passwordError")

  // Validación en tiempo real de la contraseña
  passwordInput.addEventListener("input", () => {
    const pwd = passwordInput.value
    updateValidationStatus(document.getElementById("length"), pwd.length >= 8)
    updateValidationStatus(document.getElementById("uppercase"), /[A-Z]/.test(pwd))
    updateValidationStatus(document.getElementById("lowercase"), /[a-z]/.test(pwd))
    updateValidationStatus(document.getElementById("number"), /\d/.test(pwd))
    updateValidationStatus(document.getElementById("special"), /[@$!%*?&+\-.:;,¿]/.test(pwd))

    // Oculta el mensaje de error cuando empiecen a cumplir requisitos
    if (passwordError.style.display === "block") {
      passwordError.style.display = "none"
    }
  })

  function updateValidationStatus(el, valid) {
    el.classList.toggle("valid", valid)
    el.classList.toggle("invalid", !valid)
    el.innerHTML = valid ? el.innerHTML.replace("❌", "✅") : el.innerHTML.replace("✅", "❌")
  }

  // Envío del formulario
  form.addEventListener("submit", async (e) => {
    e.preventDefault()

    const formData = {
      nombre: document.getElementById("nombre").value.trim(),
      username: document.getElementById("username").value.trim(),
      password: document.getElementById("password").value.trim(),
      correo: document.getElementById("correo").value.trim(),
    }

    // Verificar requisitos de contraseña antes de enviar
    const pwd = formData.password
    const validPassword =
      pwd.length >= 8 && /[A-Z]/.test(pwd) && /[a-z]/.test(pwd) && /\d/.test(pwd) && /[@$!%*?&+\-.:;,¿]/.test(pwd)

    if (!validPassword) {
      passwordError.style.display = "block"
      return
    }

    try {
      // Primero intentamos con la ruta API
      let response = await fetch("/api/autenticacion/registro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        // Si falla, intentamos con la ruta directa
        response = await fetch("/registro", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData),
        })
      }

      const data = await response.json()

      if (response.ok) {
        alert("Usuario registrado correctamente.")
        // Marcar onboarding pendiente
        localStorage.setItem(`onboardingCompleted_${formData.username}`, "false")
        window.location.href = "login.html"
      } else {
        alert("Error en el registro: " + (data.error || "Datos incorrectos."))
      }
    } catch (err) {
      console.error("Error de conexión con el servidor:", err)
      alert("Error de conexión con el servidor.")
    }
  })
})

// Función para mostrar u ocultar la contraseña
function togglePassword() {
  const inp = document.getElementById("password")
  inp.type = inp.type === "password" ? "text" : "password"
}
