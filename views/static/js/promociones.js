document.addEventListener("DOMContentLoaded", async () => {
  try {
    const response = await fetch("http://localhost:5000/productos");
    const productos = await response.json();

    const promoContainer = document.getElementById("promociones-container");
    promoContainer.innerHTML = "";

    // Ejemplo: agrupar productos con id 1 y id 2 en una promoción
    const promoGroup = productos.filter(p => p.id === 1 || p.id === 2);

    if (promoGroup.length > 0) {
      // Calcular el precio original sumando los precios individuales
      const precioOriginal = promoGroup.reduce((acum, prod) => acum + prod.precio, 0);
      // Aplicar un descuento (por ejemplo, 20%)
      const descuento = 0.2;
      const precioPromocional = precioOriginal * (1 - descuento);

      // Definir un objeto de promoción y guardarlo globalmente para usarlo al comprar
      window.promocionDatos = {
        id: 1001, // id único para la promoción
        nombre: `Promoción Especial: ${promoGroup.map(prod => prod.nombre).join(' + ')}`,
        precioPromocional: precioPromocional
      };

      // Crear la tarjeta de promoción con un HTML limpio y semántico
      const promoCard = document.createElement("div");
      promoCard.classList.add("promo-card");
      promoCard.innerHTML = `
        <div class="promo-images">
          ${promoGroup.map(prod => `<img src="${prod.imagen}" alt="${prod.nombre}" class="promo-image">`).join('')}
        </div>
        <h3 class="promo-title">¡Promoción Especial!</h3>
        <p class="promo-products">Incluye: ${promoGroup.map(prod => prod.nombre).join(' y ')}</p>
        <p class="promo-price">Precio Original: $${precioOriginal.toFixed(2)}</p>
        <p class="promo-discount">Descuento: 20%</p>
        <p class="promo-final-price">Precio Promocional: $${precioPromocional.toFixed(2)}</p>
        <button class="buy-promo-button" onclick="comprarPromocion()">Comprar Promoción</button>
      `;
      promoContainer.appendChild(promoCard);
    } else {
      promoContainer.innerHTML = "<p>No hay promociones disponibles en este momento.</p>";
    }
  } catch (error) {
    console.error("Error al cargar promociones:", error);
    document.getElementById("promociones-container").innerHTML = "<p>Error al cargar promociones.</p>";
  }
});


// Función para agregar la promoción al carrito y redirigir a carrito.html
function comprarPromocion() {
  let promocion = window.promocionDatos;
  if (!promocion) {
    promocion = { id: 1001, nombre: "Promoción Especial", precioPromocional: 50.00 };
  }
  let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
  const existe = carrito.find(item => item.id === promocion.id);
  if (existe) {
    existe.cantidad += 1;
  } else {
    carrito.push({ id: promocion.id, nombre: promocion.nombre, precio: promocion.precioPromocional, cantidad: 1, esPromocion: true });
  }
  localStorage.setItem("carrito", JSON.stringify(carrito));
  window.location.href = "carrito.html";
}
