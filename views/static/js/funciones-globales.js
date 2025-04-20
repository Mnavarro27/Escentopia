// Definiciones globales para funciones compartidas
function agregarAlCarrito(id, nombre, precio) {
    console.log("agregarAlCarrito llamado desde funciones-globales.js:", id, nombre, precio)
    const carrito = JSON.parse(localStorage.getItem("carrito")) || []
    const existe = carrito.find((item) => item.id === id)
    if (existe) {
      existe.cantidad++
    } else {
      carrito.push({ id, nombre, precio, cantidad: 1 })
    }
    localStorage.setItem("carrito", JSON.stringify(carrito))
    alert("Producto agregado al carrito!")
  }
  
  function mostrarDetalles(id, nombre, precio, descripcion) {
    console.log("mostrarDetalles llamado desde funciones-globales.js:", id, nombre, precio, descripcion)
    document.getElementById("modalTitulo").innerText = nombre
    document.getElementById("modalPrecio").innerText = `Precio: ${precio.toFixed(2)}`
    document.getElementById("modalDescripcion").innerText = descripcion
    document.getElementById("modalDetalles").style.display = "block"
  }
  
  // Verificar que las funciones estén disponibles globalmente
  console.log(
    "funciones-globales.js cargado. Funciones disponibles:",
    typeof agregarAlCarrito === "function",
    typeof mostrarDetalles === "function",
  )
  