document.addEventListener("DOMContentLoaded", () => {
  // Solo ejecutar si estamos en una página que no sea onboarding.html
  if (window.location.pathname.includes("onboarding.html")) return

  // Verificar si el usuario está autenticado
  const userJson = localStorage.getItem("usuario")
  if (!userJson) return // Usuario no autenticado, no hacer nada

  // Obtener el nombre de usuario
  const { username } = JSON.parse(userJson)

  // Clave específica para este usuario
  const flagKey = `onboardingCompleted_${username}`

  // Verificar si el usuario ya completó el onboarding
  if (localStorage.getItem(flagKey) !== "true") {
    console.log("Redirigiendo a onboarding para:", username)
    window.location.href = "/onboarding.html"
  } else {
    console.log("Onboarding ya completado para:", username)
  }
})
