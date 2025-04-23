// Función para obtener parámetros de la URL
function getUrlParameter(name) {
    name = name.replace(/[[]/, "\\[").replace(/[\]]/, "\\]")
    const regex = new RegExp("[\\?&]" + name + "=([^&#]*)")
    const results = regex.exec(location.search)
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "))
  }
  
  // Función para cargar tarjetas disponibles
  async function cargarTarjetas() {
    try {
      console.log("Intentando cargar tarjetas...")
      const response = await fetch("/api/simulacion/tarjetas")
  
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`)
      }
  
      const tarjetas = await response.json()
      console.log("Tarjetas recibidas:", tarjetas)
  
      const select = document.getElementById("cardSelect")
  
      // Limpiar opciones existentes
      select.innerHTML = '<option value="">Selecciona una tarjeta</option>'
  
      // Agregar tarjetas al select
      tarjetas.forEach((tarjeta) => {
        const option = document.createElement("option")
        option.value = JSON.stringify({
          numero: tarjeta.numero_tarjeta,
          fecha: tarjeta.fecha_vencimiento,
          propietario: tarjeta.propietario,
        })
        option.textContent = `${tarjeta.propietario} (${tarjeta.numero_tarjeta})`
        select.appendChild(option)
      })
    } catch (error) {
      console.error("Error al cargar tarjetas:", error)
      document.getElementById("cardSelectError").textContent = "Error al cargar tarjetas. Por favor, intenta de nuevo."
    }
  }
  
  // Función para autocompletar datos de tarjeta
  function autocompletarTarjeta() {
    const select = document.getElementById("cardSelect")
    const selectedValue = select.value
  
    if (!selectedValue) {
      // Limpiar campos si no hay selección
      document.getElementById("cardHolder").value = ""
      document.getElementById("cardNumber").value = ""
      document.getElementById("cardExpiry").value = ""
      return
    }
  
    try {
      const tarjeta = JSON.parse(selectedValue)
      document.getElementById("cardHolder").value = tarjeta.propietario
      document.getElementById("cardNumber").value = tarjeta.numero
      document.getElementById("cardExpiry").value = tarjeta.fecha
    } catch (error) {
      console.error("Error al autocompletar tarjeta:", error)
    }
  }
  
  // Función para procesar pago con tarjeta
  async function procesarPagoTarjeta() {
    const select = document.getElementById("cardSelect")
    const selectedValue = select.value
  
    if (!selectedValue) {
      document.getElementById("cardSelectError").textContent = "Por favor, selecciona una tarjeta."
      return
    }
  
    try {
      const tarjeta = JSON.parse(selectedValue)
  
      // Deshabilitar botón mientras se procesa
      const payBtn = document.getElementById("payWithCardBtn")
      payBtn.disabled = true
      payBtn.textContent = "Procesando..."
  
      // Enviar solicitud de pago
      const response = await fetch("/api/simulacion/validar-pago", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          numero: tarjeta.numero,
          fecha_vencimiento: tarjeta.fecha,
          monto: totalAmount,
        }),
      })
  
      const data = await response.json()
  
      // Habilitar botón nuevamente
      payBtn.disabled = false
      payBtn.textContent = "Pagar con Tarjeta"
  
      if (response.ok && data.validacion === "aprobada") {
        // Mostrar modal de confirmación
        document.getElementById("orderNumber").textContent = Math.floor(100000 + Math.random() * 900000)
        document.getElementById("paidAmount").textContent = totalAmount.toFixed(2)
        document.getElementById("paymentConfirmationModal").style.display = "block"
  
        // Limpiar carrito
        localStorage.removeItem("carrito")
      } else {
        document.getElementById("cardPaymentError").textContent =
          data.motivo || "Error al procesar el pago. Por favor, intenta con otra tarjeta."
      }
    } catch (error) {
      console.error("Error al procesar pago:", error)
      document.getElementById("cardPaymentError").textContent =
        "Error al conectar con el servidor. Por favor, intenta de nuevo."
  
      // Habilitar botón nuevamente
      document.getElementById("payWithCardBtn").disabled = false
      document.getElementById("payWithCardBtn").textContent = "Pagar con Tarjeta"
    }
  }
  
  // Función para iniciar pago con PayPal
  async function iniciarPagoPaypal() {
    try {
      // Deshabilitar botón mientras se procesa
      const payBtn = document.getElementById("payWithPaypalBtn")
      payBtn.disabled = true
      payBtn.textContent = "Procesando..."
  
      // Enviar solicitud para crear pago en PayPal
      const response = await fetch("/api/paypal/create-payment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          monto: totalAmount,
        }),
      })
  
      const data = await response.json()
  
      // Habilitar botón nuevamente
      payBtn.disabled = false
      payBtn.textContent = "Pagar con PayPal"
  
      if (response.ok && data.redirectUrl) {
        // Redirigir a PayPal
        window.location.href = data.redirectUrl
      } else {
        document.getElementById("paypalPaymentError").textContent =
          data.error || "Error al iniciar el pago con PayPal. Por favor, intenta de nuevo."
      }
    } catch (error) {
      console.error("Error al iniciar pago con PayPal:", error)
      document.getElementById("paypalPaymentError").textContent =
        "Error al conectar con el servidor. Por favor, intenta de nuevo."
  
      // Habilitar botón nuevamente
      document.getElementById("payWithPaypalBtn").disabled = false
      document.getElementById("payWithPaypalBtn").textContent = "Pagar con PayPal"
    }
  }
  
  // Variables globales
  let totalAmount = 0
  
  // Event listeners
  document.addEventListener("DOMContentLoaded", () => {
    // Obtener total de la URL
    const total = getUrlParameter("total")
    if (total) {
      totalAmount = Number.parseFloat(total)
      document.getElementById("totalAmount").textContent = totalAmount.toFixed(2)
    } else {
      // Redirigir al carrito si no hay total
      window.location.href = "/carrito.html"
    }
  
    // Cargar tarjetas disponibles
    cargarTarjetas()
  
    // Event listener para cambio de tarjeta
    document.getElementById("cardSelect").addEventListener("change", autocompletarTarjeta)
  
    // Event listener para botón de pago con tarjeta
    document.getElementById("payWithCardBtn").addEventListener("click", procesarPagoTarjeta)
  
    // Event listener para botón de pago con PayPal
    document.getElementById("payWithPaypalBtn").addEventListener("click", iniciarPagoPaypal)
  
    // Event listeners para cambio de método de pago
    document.querySelectorAll(".payment-method").forEach((method) => {
      method.addEventListener("click", function () {
        // Actualizar radio button
        this.querySelector('input[type="radio"]').checked = true
  
        // Actualizar clases activas
        document.querySelectorAll(".payment-method").forEach((m) => m.classList.remove("active"))
        this.classList.add("active")
  
        // Mostrar formulario correspondiente
        const methodType = this.dataset.method
        document.querySelectorAll(".payment-form").forEach((form) => form.classList.remove("active"))
        document.getElementById(`${methodType}PaymentForm`).classList.add("active")
      })
    })
  
    // Event listener para cerrar modal
    document.querySelector("#paymentConfirmationModal .close").addEventListener("click", () => {
      document.getElementById("paymentConfirmationModal").style.display = "none"
    })
  
    // Event listener para botón de continuar comprando
    document.getElementById("continueShoppingBtn").addEventListener("click", () => {
      window.location.href = "/index.html"
    })
  })
  