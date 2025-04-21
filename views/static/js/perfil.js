document.addEventListener("DOMContentLoaded", async () => {
    const storedUser = localStorage.getItem("usuario")
  
    if (!storedUser) {
      alert("Debes iniciar sesión primero.")
      window.location.href = "login.html"
      return
    }
  
    const usuario = JSON.parse(storedUser)
    
  
    try {
      const response = await fetch(`http://localhost:5000/perfil?username=${encodeURIComponent(usuario.username)}`)
      const data = await response.json()
      if (!data.username) throw new Error("No se recibieron datos válidos del perfil.")
  
      // Rellenar Información Básica
      document.getElementById("nombre").value = data.nombre || ""
      document.getElementById("apellido").value = data.apellido || ""
      document.getElementById("tipoIdentificacion").value = data.tipo_identificacion || ""
      document.getElementById("identificacion").value = data.identificacion || ""
      document.getElementById("correo").value = data.correo || ""
      document.getElementById("telefono").value = data.telefono || ""
      document.getElementById("username").value = data.username || ""
  
      // Rellenar Información Adicional (si existe)
      document.getElementById("fechaNacimiento").value = data.fecha_nacimiento ? data.fecha_nacimiento.split("T")[0] : ""
      document.getElementById("sexo").value = data.sexo || ""
      document.getElementById("direccion").value = data.direccion || ""
      document.getElementById("nombreTarjeta").value = data.nombre_tarjeta || ""
      document.getElementById("numeroTarjeta").value = data.numero_tarjeta || ""
      document.getElementById("fechaVencimiento").value = data.fecha_vencimiento || ""
      document.getElementById("codigoSeguridad").value = data.codigo_seguridad || ""
  
      // Cargar selectores de ubicación con la lógica habitual
      await cargarPaises(data.pais_id)
      await cargarProvincias(data.pais_id, data.provincia_id)
      await cargarCantones(data.provincia_id, data.canton_id)
      await cargarDistritos(data.canton_id, data.distrito_id)
    } catch (error) {
      console.error("Error al cargar el perfil:", error)
      alert("No se pudieron cargar los datos del perfil.")
    }
  
    // Evento para desplegar/ocultar la sección de información adicional con animación
    document.getElementById("verificar-btn").addEventListener("click", () => {
      const additionalInfoDiv = document.getElementById("additional-info")
  
      if (additionalInfoDiv.style.display === "none" || !additionalInfoDiv.style.display) {
        additionalInfoDiv.style.display = "block"
        // Pequeño retraso para que la transición funcione correctamente
        setTimeout(() => {
          additionalInfoDiv.classList.add("active")
        }, 10)
        document.getElementById("verificar-btn").textContent = "Ocultar información adicional"
      } else {
        additionalInfoDiv.classList.remove("active")
        // Esperar a que termine la transición antes de ocultar el elemento
        setTimeout(() => {
          additionalInfoDiv.style.display = "none"
        }, 500) // Este tiempo debe coincidir con la duración de la transición en CSS
        document.getElementById("verificar-btn").textContent = "Verificar Perfil"
      }
    })
  })
  
  // Funciones para cargar la información de ubicación
  async function cargarPaises(selectedPais) {
    try {
      const response = await fetch("http://localhost:5000/paises")
      const data = await response.json()
      const paisSelect = document.getElementById("pais")
      paisSelect.innerHTML = '<option value="">Seleccione un país</option>'
      data.forEach((pais) => {
        const option = document.createElement("option")
        option.value = pais.id
        option.textContent = pais.nombre
        if (pais.id === selectedPais) option.selected = true
        paisSelect.appendChild(option)
      })
    } catch (error) {
      console.error("Error al cargar países:", error)
    }
  }
  
  // Evento para cambio de país
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("pais").addEventListener("change", async (event) => {
      const paisId = event.target.value
      await cargarProvincias(paisId)
      // Limpiar los selectores dependientes
      document.getElementById("canton").innerHTML = '<option value="">Seleccione un cantón</option>'
      document.getElementById("distrito").innerHTML = '<option value="">Seleccione un distrito</option>'
    })
  })
  
  async function cargarProvincias(paisId, selectedProvincia) {
    if (!paisId) return
    try {
      const response = await fetch(`http://localhost:5000/provincias?pais=${paisId}`)
      const data = await response.json()
      const provinciaSelect = document.getElementById("provincia")
      provinciaSelect.innerHTML = '<option value="">Seleccione una provincia</option>'
      data.forEach((provincia) => {
        const option = document.createElement("option")
        option.value = provincia.id
        option.textContent = provincia.nombre
        if (provincia.id === selectedProvincia) option.selected = true
        provinciaSelect.appendChild(option)
      })
    } catch (error) {
      console.error("Error al cargar provincias:", error)
    }
  }
  
  // Evento para cambio de provincia
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("provincia").addEventListener("change", async (event) => {
      const provinciaId = event.target.value
      await cargarCantones(provinciaId)
      // Limpiar el selector de distrito
      document.getElementById("distrito").innerHTML = '<option value="">Seleccione un distrito</option>'
    })
  })
  
  async function cargarCantones(provinciaId, selectedCanton) {
    if (!provinciaId) return
    try {
      const response = await fetch(`http://localhost:5000/cantones?provincia=${provinciaId}`)
      const data = await response.json()
      const cantonSelect = document.getElementById("canton")
      cantonSelect.innerHTML = '<option value="">Seleccione un cantón</option>'
      data.forEach((canton) => {
        const option = document.createElement("option")
        option.value = canton.id
        option.textContent = canton.nombre
        if (canton.id === selectedCanton) option.selected = true
        cantonSelect.appendChild(option)
      })
    } catch (error) {
      console.error("Error al cargar cantones:", error)
    }
  }
  
  // Evento para cambio de cantón
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("canton").addEventListener("change", async (event) => {
      const cantonId = event.target.value
      await cargarDistritos(cantonId)
    })
  })
  
  async function cargarDistritos(cantonId, selectedDistrito) {
    if (!cantonId) return
    try {
      const response = await fetch(`http://localhost:5000/distritos?canton=${cantonId}`)
      const data = await response.json()
      const distritoSelect = document.getElementById("distrito")
      distritoSelect.innerHTML = '<option value="">Seleccione un distrito</option>'
      data.forEach((distrito) => {
        const option = document.createElement("option")
        option.value = distrito.id
        option.textContent = distrito.nombre
        if (distrito.id === selectedDistrito) option.selected = true
        distritoSelect.appendChild(option)
      })
    } catch (error) {
      console.error("Error al cargar distritos:", error)
    }
  }
  
  // Evento para enviar el formulario y actualizar el perfil
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("perfil-form").addEventListener("submit", async (e) => {
      e.preventDefault()
  
      const storedUser = localStorage.getItem("usuario")
      if (!storedUser) {
        alert("Debes iniciar sesión primero.")
        window.location.href = "login.html"
        return
      }
      const usuario = JSON.parse(storedUser)
  
      // Recoger datos básicos
      const updatedData = {
        username: usuario.username,
        nombre: document.getElementById("nombre").value.trim(),
        apellido: document.getElementById("apellido").value.trim(),
        tipoIdentificacion: document.getElementById("tipoIdentificacion").value,
        identificacion: document.getElementById("identificacion").value.trim(),
        correo: document.getElementById("correo").value.trim(),
        telefono: document.getElementById("telefono").value.trim(),
      }
  
      // Si la sección adicional se encuentra visible, recoger esos datos
      if (document.getElementById("additional-info").style.display !== "none") {
        updatedData.fechaNacimiento = document.getElementById("fechaNacimiento").value
        updatedData.sexo = document.getElementById("sexo").value
        updatedData.direccion = document.getElementById("direccion").value.trim()
        updatedData.pais = document.getElementById("pais").value
        updatedData.provincia = document.getElementById("provincia").value
        updatedData.canton = document.getElementById("canton").value
        updatedData.distrito = document.getElementById("distrito").value
        updatedData.nombreTarjeta = document.getElementById("nombreTarjeta").value.trim()
        updatedData.numeroTarjeta = document.getElementById("numeroTarjeta").value.trim()
        updatedData.fechaVencimiento = document.getElementById("fechaVencimiento").value
        updatedData.codigoSeguridad = document.getElementById("codigoSeguridad").value.trim()
      }
  
      try {
        const response = await fetch("http://localhost:5000/perfil", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatedData),
        })
        const data = await response.json()
        if (response.ok) {
          alert("Perfil actualizado correctamente.")
          window.location.href = "index.html"
        } else {
          alert("Error al actualizar el perfil: " + (data.error || "Error desconocido."))
        }
      } catch (error) {
        console.error("Error en la actualización:", error)
        alert("Error de conexión con el servidor.")
      }
    })
  })
  