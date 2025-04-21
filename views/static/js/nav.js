document.addEventListener("DOMContentLoaded", function () {
  console.log("nav.js cargado correctamente");
  // Dropdown de “Ver Promociones”
  const menuButton   = document.getElementById("menu-button");
  const menuDropdown = document.getElementById("menu-dropdown");

  menuButton.addEventListener("click", function (e) {
    e.stopPropagation();
    menuDropdown.classList.toggle("active");
  });

  document.addEventListener("click", function (e) {
    if (!menuDropdown.contains(e.target) && e.target !== menuButton) {
      menuDropdown.classList.remove("active");
    }
  });

  // Carrito, perfil y logout
  const cartButton   = document.getElementById("cart-button");
  const userButton   = document.getElementById("user-button");
  const logoutButton = document.getElementById("logout-button");

  if (cartButton)   cartButton.addEventListener("click", () => window.location.href = "carrito.html");
  if (userButton)   userButton.addEventListener("click", () => window.location.href = "perfil.html");
  if (logoutButton) logoutButton.addEventListener("click", () => {
    localStorage.removeItem("usuario");
    localStorage.removeItem("usuario_temp");
    window.location.href = "login.html";
  });

  
  // Destacar categoría activa
  const currentPage   = window.location.pathname.split("/").pop();
  document.querySelectorAll(".category-menu a")
    .forEach(link => link.classList.toggle("active-category",
      link.getAttribute("href") === currentPage
    ));
});
