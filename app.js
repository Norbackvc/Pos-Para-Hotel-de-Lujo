// NOTE: These are demo credentials for a static prototype only.
// In a production environment, authentication must be handled server-side.
const CREDENCIALES = {
  admin: "hotel123",
  cajero: "cajero456",
};

/**
 * Muestra el panel principal y oculta la sección de inicio.
 * @param {string} usuario - Nombre del usuario que inició sesión.
 */
function mostrarPanel(usuario) {
  document.getElementById("inicio").classList.add("oculto");
  const panel = document.getElementById("panel");
  panel.classList.remove("oculto");
  document.getElementById("nombre-usuario").textContent = usuario;
}

/**
 * Valida las credenciales y, de ser correctas, inicia sesión.
 */
function iniciarSesion() {
  const usuario = document.getElementById("usuario").value.trim();
  const contrasena = document.getElementById("contrasena").value;
  const errorMsg = document.getElementById("error-msg");

  errorMsg.textContent = "";

  if (!usuario || !contrasena) {
    errorMsg.textContent = "Por favor complete todos los campos.";
    return;
  }

  if (CREDENCIALES[usuario] && CREDENCIALES[usuario] === contrasena) {
    mostrarPanel(usuario);
  } else {
    errorMsg.textContent = "Usuario o contraseña incorrectos.";
    document.getElementById("contrasena").value = "";
  }
}

/**
 * Cierra la sesión y vuelve a la sección de inicio.
 */
function cerrarSesion() {
  document.getElementById("panel").classList.add("oculto");
  document.getElementById("inicio").classList.remove("oculto");
  document.getElementById("usuario").value = "";
  document.getElementById("contrasena").value = "";
  document.getElementById("error-msg").textContent = "";
}

// Attach event listeners after DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-ingresar").addEventListener("click", iniciarSesion);
  document.getElementById("btn-cerrar-sesion").addEventListener("click", cerrarSesion);

  document.getElementById("contrasena").addEventListener("keydown", (e) => {
    if (e.key === "Enter") iniciarSesion();
  });
  document.getElementById("usuario").addEventListener("keydown", (e) => {
    if (e.key === "Enter") iniciarSesion();
  });
});
