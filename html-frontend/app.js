// app.js - Sistema de códigos de verificación

function formatearHora(hora) {
  if (typeof hora === 'number') {
    const totalSegundos = Math.floor(hora);
    const horas = String(Math.floor(totalSegundos / 3600)).padStart(2, '0');
    const minutos = String(Math.floor((totalSegundos % 3600) / 60)).padStart(2, '0');
    const segundos = String(totalSegundos % 60).padStart(2, '0');
    return `${horas}:${minutos}:${segundos}`;
  }
  return hora || "??:??";
}

// 📊 Función para mostrar información de tokens
function mostrarTokens(tokens, contenedorId) {
  const contenedor = document.getElementById(contenedorId);
  if (!tokens || !contenedor) return;
  
  let html = '<div class="alert alert-info mt-2">';
  html += '<small><strong>🔢 Tokens usados:</strong><br>';
  
  for (const [tipo, cantidad] of Object.entries(tokens)) {
    if (tipo !== 'total') {
      html += `${tipo}: ${cantidad} | `;
    }
  }
  html += `<strong>Total: ${tokens.total}</strong></small></div>`;
  
  contenedor.innerHTML = html;
}

// 🎨 Función para formatear respuestas de GPT con mejor estilo
function formatearRespuestaGPT(texto) {
  if (!texto) return texto;
  
  // Convertir markdown básico a HTML con estilos bonitos
  let html = texto
    // Títulos con emojis
    .replace(/📊 \*\*(.*?)\*\*/g, '<div class="alert alert-info mt-3 mb-2"><strong>📊 $1</strong></div>')
    .replace(/🗓️ \*\*(.*?)\*\*/g, '<div class="alert alert-primary mt-3 mb-2"><strong>🗓️ $1</strong></div>')
    .replace(/📈 \*\*(.*?)\*\*/g, '<div class="alert alert-success mt-3 mb-2"><strong>📈 $1</strong></div>')
    // Otros títulos con negritas
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Bullets con mejor espaciado
    .replace(/• \*\*(.*?)\*\* - (.*?) \[(.*?)\]/g, 
             '<li class="list-group-item border-0 py-2"><strong class="text-primary">$1</strong> - $2 <span class="badge bg-light text-dark ms-2">$3</span></li>')
    .replace(/• (.*?)$/gm, '<li class="list-group-item border-0 py-1">$1</li>')
    // Saltos de línea
    .replace(/\n\n/g, '</ul><br><ul class="list-group list-group-flush">')
    .replace(/\n/g, '<br>');
  
  // Envolver bullets en lista si las hay
  if (html.includes('<li class="list-group-item')) {
    html = '<ul class="list-group list-group-flush">' + html + '</ul>';
  }
  
  return html;
}

// 💰 Función para calcular costo estimado
function calcularCosto(tokens) {
  // Precios por 1K tokens (julio 2025)
  const precios = {
    "gpt-3.5-turbo": { input: 0.0005, output: 0.0015 },
    "gpt-4": { input: 0.03, output: 0.06 },
    "text-embedding-3-small": 0.00002
  };
  
  // Estimación (asumiendo 50% input, 50% output para chat)
  const costoEmbedding = (tokens.embedding || 0) * precios["text-embedding-3-small"] / 1000;
  const costoChat = ((tokens.enriquecimiento || 0) + (tokens.resumen_final || 0)) * 
                   (precios["gpt-4"].input + precios["gpt-4"].output) / 2000;
  
  return (costoEmbedding + costoChat).toFixed(6);
}

// 🗑️ Función para borrar una nota
async function borrarNota(notaId, titulo) {
  const confirmMsg = `¿Estás seguro de borrar la nota "${titulo}"?\n\nEsta acción no se puede deshacer.`;
  
  if (!confirm(confirmMsg)) {
    return;
  }
  
  try {
    const res = await fetch(`https://notasia.1963.com.ar/borrar-nota/${notaId}`, {
      method: 'DELETE'
    });
    
    const result = await res.json();
    
    if (result.status === 'ok') {
      // Mostrar mensaje de éxito
      mostrarMensajeFlotante(`✅ Nota "${titulo}" borrada correctamente`, 'success');
      
      // Recargar historial automáticamente
      document.getElementById('cargarHistorial').click();
    } else {
      mostrarMensajeFlotante(`❌ Error: ${result.message}`, 'danger');
    }
  } catch (error) {
    mostrarMensajeFlotante(`⚠️ Error de conexión: ${error.message}`, 'danger');
  }
}

// 💬 Mostrar mensajes flotantes
function mostrarMensajeFlotante(mensaje, tipo = 'info') {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
  alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
  alertDiv.innerHTML = `
    ${mensaje}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  document.body.appendChild(alertDiv);
  
  // Auto-remover después de 4 segundos
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 4000);
}

// 🔐 Funciones de autenticación
function isAuthenticated() {
  const sessionToken = localStorage.getItem("session_token");
  const userEmail = localStorage.getItem("user_email");
  return sessionToken && userEmail;
}

function logout() {
  localStorage.removeItem("session_token");
  localStorage.removeItem("user_email");
  localStorage.removeItem("session_expires");
  location.reload();
}

// 📧 Función para enviar código de verificación
async function enviarCodigo(email) {
  const resultadoDiv = document.getElementById("resultadoEnvio");
  const botonEnviar = document.getElementById("enviarCodigo");
  
  try {
    botonEnviar.innerHTML = "⏳ Enviando código...";
    botonEnviar.disabled = true;
    resultadoDiv.innerHTML = "";
    
    const res = await fetch("https://notasia.1963.com.ar/enviar-codigo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email })
    });
    
    const data = await res.json();
    
    if (data.status === "ok") {
      resultadoDiv.innerHTML = `
        <div class="alert alert-success">
          <strong>📧 ¡Código enviado!</strong><br>
          ${data.message}<br>
          <small class="text-muted">⏰ El código expira en 10 minutos</small>
        </div>
      `;
      
      // Cambiar al paso de código
      document.getElementById("stepEmail").classList.remove("active");
      document.getElementById("stepCodigo").classList.add("active");
      document.getElementById("emailDestino").textContent = email;
      
      // Enfocar el campo de código
      setTimeout(() => {
        document.getElementById("codigoVerificacion").focus();
      }, 100);
      
    } else {
      resultadoDiv.innerHTML = `
        <div class="alert alert-danger">
          <strong>❌ Error:</strong> ${data.message}
        </div>
      `;
    }
  } catch (error) {
    resultadoDiv.innerHTML = `
      <div class="alert alert-danger">
        <strong>⚠️ Error de conexión:</strong> ${error.message}
      </div>
    `;
  } finally {
    botonEnviar.innerHTML = "📧 Enviar Código";
    botonEnviar.disabled = false;
  }
}

// 🔢 Función para verificar código
async function verificarCodigo(email, codigo) {
  const resultadoDiv = document.getElementById("resultadoVerificacion");
  const botonVerificar = document.getElementById("verificarCodigo");
  
  try {
    botonVerificar.innerHTML = "⏳ Verificando...";
    botonVerificar.disabled = true;
    resultadoDiv.innerHTML = "";
    
    const res = await fetch("https://notasia.1963.com.ar/verificar-codigo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, codigo: codigo })
    });
    
    const data = await res.json();
    
    if (data.status === "ok") {
      // Guardar datos de sesión
      localStorage.setItem("session_token", data.session_token);
      localStorage.setItem("user_email", data.email);
      localStorage.setItem("session_expires", data.expires_at);
      
      resultadoDiv.innerHTML = `
        <div class="alert alert-success">
          <h6>✅ ¡Código verificado!</h6>
          <p>Bienvenido <strong>${data.email}</strong></p>
          <p><small>Redirigiendo...</small></p>
        </div>
      `;
      
      // Recargar la página para mostrar la app
      setTimeout(() => {
        location.reload();
      }, 1500);
      
    } else {
      resultadoDiv.innerHTML = `
        <div class="alert alert-danger">
          <strong>❌ Error:</strong> ${data.message}
        </div>
      `;
    }
  } catch (error) {
    resultadoDiv.innerHTML = `
      <div class="alert alert-danger">
        <strong>⚠️ Error de conexión:</strong> ${error.message}
      </div>
    `;
  } finally {
    botonVerificar.innerHTML = "🔓 Verificar Código";
    botonVerificar.disabled = false;
  }
}

// 🎯 Configurar eventos de autenticación
function configurarEventosAuth() {
  // Enviar código
  document.getElementById("enviarCodigo").addEventListener("click", () => {
    const email = document.getElementById("loginEmail").value.trim();
    if (email && email.includes("@")) {
      enviarCodigo(email);
    } else {
      mostrarMensajeFlotante("❌ Ingresa un email válido", 'danger');
    }
  });
  
  // Enter key en el campo email
  document.getElementById("loginEmail").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      document.getElementById("enviarCodigo").click();
    }
  });
  
  // Verificar código
  document.getElementById("verificarCodigo").addEventListener("click", () => {
    const email = document.getElementById("loginEmail").value.trim();
    const codigo = document.getElementById("codigoVerificacion").value.trim();
    
    if (codigo.length !== 6 || !codigo.match(/^\d{6}$/)) {
      mostrarMensajeFlotante("❌ El código debe tener 6 dígitos", 'danger');
      return;
    }
    
    verificarCodigo(email, codigo);
  });
  
  // Enter key en el campo código
  document.getElementById("codigoVerificacion").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      document.getElementById("verificarCodigo").click();
    }
  });
  
  // Auto-formatear código mientras se escribe
  document.getElementById("codigoVerificacion").addEventListener("input", (e) => {
    let value = e.target.value.replace(/\D/g, ''); // Solo números
    if (value.length > 6) value = value.slice(0, 6);
    e.target.value = value;
  });
  
  // Botón para volver al paso de email
  document.getElementById("volverEmail").addEventListener("click", () => {
    document.getElementById("stepCodigo").classList.remove("active");
    document.getElementById("stepEmail").classList.add("active");
    document.getElementById("codigoVerificacion").value = "";
    document.getElementById("resultadoVerificacion").innerHTML = "";
  });
}

// 📝 Configurar funcionalidad de notas
function configurarFuncionalidadNotas() {
  // Geolocalización
  navigator.geolocation.getCurrentPosition((position) => {
    localStorage.setItem("geo_lat", position.coords.latitude);
    localStorage.setItem("geo_lon", position.coords.longitude);
    const latInput = document.getElementById("latitud");
    const lonInput = document.getElementById("longitud");
    if (latInput && lonInput) {
      latInput.value = position.coords.latitude;
      lonInput.value = position.coords.longitude;
    }
  }, (err) => {
    const geoStatus = document.getElementById("geo-status");
    if (geoStatus) {
      geoStatus.textContent = "No se pudo obtener ubicación.";
    }
  });

  // Formulario de nueva nota
  const notaForm = document.getElementById("notaForm");
  if (notaForm) {
    notaForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fechaManualInput = document.getElementById("fechaManual");
      const resultadoDiv = document.getElementById("resultado");
      
      // Limpiar resultados anteriores
      resultadoDiv.innerHTML = "⏳ Guardando nota...";
      const tokensDiv = document.getElementById("tokensGuardar");
      if (tokensDiv) tokensDiv.innerHTML = "";
      
      const payload = {
        user_email: localStorage.getItem("user_email"),
        texto: document.getElementById("texto").value.trim(),
        emocion: document.getElementById("emocion").value.trim() || undefined,
        tags: document.getElementById("tags").value.trim().split(",").filter(tag => tag.trim()),
        categoria: document.getElementById("categoria").value.trim() || undefined,
        ubicacion_textual: document.getElementById("ubicacion").value.trim() || undefined,
        latitud: parseFloat(localStorage.getItem("geo_lat")) || undefined,
        longitud: parseFloat(localStorage.getItem("geo_lon")) || undefined,
        fecha_manual: fechaManualInput ? fechaManualInput.value : undefined,
      };

      try {
        const res = await fetch("https://notasia.1963.com.ar/guardar-nota", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        
        if (res.ok && data.status === "ok") {
          const costo = calcularCosto(data.tokens_usados || {});
          resultadoDiv.innerHTML = `
            ✅ Nota guardada con éxito.
            <small class="text-muted d-block">💰 Costo estimado: ${costo} USD</small>
          `;
          mostrarTokens(data.tokens_usados, "tokensGuardar");
          notaForm.reset();
        } else {
          resultadoDiv.textContent = "❌ Error al guardar la nota.";
        }
      } catch (err) {
        resultadoDiv.textContent = "⚠️ Error al conectar con el servidor.";
      }
    });
  }

  // Cargar historial
  const btnHistorial = document.getElementById("cargarHistorial");
  if (btnHistorial) {
    btnHistorial.addEventListener("click", async () => {
      const contenedor = document.getElementById("resultadoHistorial");
      contenedor.innerHTML = "⏳ Cargando...";
      try {
        const emailGuardado = localStorage.getItem("user_email");
        const res = await fetch(`https://notasia.1963.com.ar/notas-por-email?email=${encodeURIComponent(emailGuardado)}`);
        const data = await res.json();
        contenedor.innerHTML = "";
        if (data.notas && data.notas.length > 0) {
          data.notas.forEach(nota => {
            const div = document.createElement("div");
            div.className = "card mb-2";
            const horaLegible = formatearHora(nota.hora);
            const titulo = nota.titulo || nota.texto?.slice(0, 40) || "(sin título)";
            const fechaFormateada = new Date(nota.fecha + 'T00:00:00').toLocaleDateString('es-AR');
            
            div.innerHTML = `
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div class="flex-grow-1">
                    <h6 class="card-title mb-1">${titulo}</h6>
                    <small class="text-muted">${fechaFormateada} ${horaLegible}</small>
                    <p class="card-text mt-2">${nota.texto}</p>
                    <div class="d-flex gap-2">
                      ${nota.emocion ? `<span class="badge bg-primary">${nota.emocion}</span>` : ''}
                      ${nota.categoria ? `<span class="badge bg-secondary">${nota.categoria}</span>` : ''}
                      ${nota.ubicacion_textual ? `<small class="text-muted">📍 ${nota.ubicacion_textual}</small>` : ''}
                    </div>
                  </div>
                  <div class="ms-3">
                    <button class="btn btn-outline-danger btn-sm" onclick="borrarNota(${nota.id}, '${titulo.replace(/'/g, "\\'")}')">
                      🗑️ Borrar
                    </button>
                  </div>
                </div>
              </div>
            `;
            contenedor.appendChild(div);
          });
        } else {
          contenedor.textContent = "📭 No se encontraron notas.";
        }
      } catch {
        contenedor.textContent = "⚠️ Error al obtener historial.";
      }
    });
  }

  // Buscar notas
  const btnBuscar = document.getElementById("buscarNotas");
  if (btnBuscar) {
    btnBuscar.addEventListener("click", async () => {
      const texto = document.getElementById("textoBuscar").value.trim();
      const contenedor = document.getElementById("resultadoBusqueda");
      const offsetMin = new Date().getTimezoneOffset();
      const offsetHoras = -offsetMin / 60;

      contenedor.innerHTML = "🔎 Buscando...";
      const tokensBusquedaDiv = document.getElementById("tokensBusqueda");
      if (tokensBusquedaDiv) tokensBusquedaDiv.innerHTML = "";
      
      try {
        const emailGuardado = localStorage.getItem("user_email");
        const res = await fetch(
          `https://notasia.1963.com.ar/buscar-notas?email=${encodeURIComponent(emailGuardado)}&texto=${encodeURIComponent(texto)}&offset=${offsetHoras}`
        );
        const data = await res.json();
        contenedor.innerHTML = "";
        
        // 📊 Mostrar información de tokens
        if (data.tokens_usados) {
          const costo = calcularCosto(data.tokens_usados);
          mostrarTokens(data.tokens_usados, "tokensBusqueda");
          
          // Agregar costo al final del contenedor de tokens
          const tokensDiv = document.getElementById("tokensBusqueda");
          if (tokensDiv && tokensDiv.innerHTML) {
            tokensDiv.innerHTML = tokensDiv.innerHTML.replace(
              '</div>', 
              `<br><strong>💰 Costo estimado: ${costo} USD</strong></div>`
            );
          }
        }
        
        if (data.resumen) {
          const resumen = document.createElement("div");
          resumen.className = "card mt-3";
          resumen.innerHTML = `
            <div class="card-header bg-success text-white">
              <strong>🧠 Asistente Personal</strong>
            </div>
            <div class="card-body">
              ${formatearRespuestaGPT(data.resumen)}
            </div>
          `;
          contenedor.appendChild(resumen);
        }
        
        if (data.resultados && data.resultados.length > 0) {
          data.resultados.forEach(nota => {
            const div = document.createElement("div");
            div.className = "border p-2 mb-2";

            const horaLegible = formatearHora(nota.hora);
            const titulo = nota.titulo || nota.texto?.slice(0, 40) || "(sin título)";
            const tags = Array.isArray(nota.tags) ? nota.tags.join(", ") : nota.tags || "";

            div.innerHTML = `
              <details>
                <summary>📝 <strong>${titulo}</strong><br><small>${nota.fecha} ${horaLegible}</small></summary>
                <div class="mt-2">
                  <div>${nota.texto}</div>
                  <ul class="mt-2 small">
                    <li><strong>ID:</strong> ${nota.pinecone_id || nota.id}</li>
                    <li><strong>Namespace:</strong> ${nota.namespace || "__default__"}</li>
                    <li><strong>Categoría:</strong> ${nota.categoria || "—"}</li>
                    <li><strong>Emoción:</strong> ${nota.emocion || "—"}</li>
                    <li><strong>Ubicación:</strong> ${nota.ubicacion_textual || "—"}</li>
                    <li><strong>Tags:</strong> ${tags || "—"}</li>
                    <li><strong>Resumen:</strong> ${nota.resumen || "—"}</li>
                    <li><strong>Score:</strong> ${nota.score?.toFixed(3) || "—"}</li>
                  </ul>
                </div>
              </details>
            `;
            contenedor.appendChild(div);
          });
        } else {
          contenedor.innerHTML += "<p>📭 No se encontraron notas relevantes.</p>";
        }
      } catch {
        contenedor.textContent = "⚠️ Error al realizar la búsqueda.";
      }
    });
  }
}

// 🗺️ Configurar funcionalidad del mapa
function configurarMapa() {
  async function cargarMapa() {
    const contenedor = document.getElementById("mapaContainer");
    if (!contenedor) return;
    
    contenedor.innerHTML = "⏳ Cargando mapa...";

    try {
      const emailGuardado = localStorage.getItem("user_email");
      const res = await fetch(`https://notasia.1963.com.ar/mapa-notas?email=${encodeURIComponent(emailGuardado)}`);
      const data = await res.json();

      contenedor.innerHTML = "";

      if (window._mapaInstance) {
        window._mapaInstance.remove();
        window._mapaInstance = null;
      }

      const notasPorUbicacion = {};
      data.notas.forEach(nota => {
        const key = `${nota.latitud},${nota.longitud}`;
        if (!notasPorUbicacion[key]) notasPorUbicacion[key] = [];
        notasPorUbicacion[key].push(nota);
      });

      const map = L.map("mapaContainer").setView([-34.6, -58.4], 11);
      window._mapaInstance = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      for (const key in notasPorUbicacion) {
        const [lat, lon] = key.split(",");
        const notas = notasPorUbicacion[key];
        const popupHtml = notas.map(n => `<strong>${n.fecha} ${n.hora}</strong><br>${n.texto}`).join("<hr>");
        const marker = L.marker([parseFloat(lat), parseFloat(lon)]).addTo(map);
        marker.bindPopup(popupHtml);
      }

      setTimeout(() => {
        map.invalidateSize();
      }, 300);

    } catch (err) {
      contenedor.innerHTML = "⚠️ Error al cargar el mapa.";
      console.error("Error al cargar mapa:", err);
    }
  }

  let mapaYaCargado = false;
  const btnMapa = document.querySelector('button[data-bs-target="#mapa"]');
  if (btnMapa) {
    btnMapa.addEventListener('shown.bs.tab', () => {
      if (!mapaYaCargado) {
        cargarMapa();
        mapaYaCargado = true;
      }
    });
  }

  const btnRefrescar = document.getElementById("refrescarMapa");
  if (btnRefrescar) {
    btnRefrescar.addEventListener("click", () => {
      cargarMapa();
    });
  }
}

// 🚀 Inicialización principal
document.addEventListener("DOMContentLoaded", () => {
  const sesionInfo = document.getElementById("sesionInfo");
  const loginSection = document.getElementById("loginSection");

  const mostrarUsuarioAutenticado = (email) => {
    if (sesionInfo) {
      sesionInfo.innerHTML = `
        <div>
          <small>Sesión activa:</small><br>
          <strong>${email}</strong>
          <button class="btn btn-sm btn-outline-danger ms-2" id="cerrarSesion">🔓 Cerrar sesión</button>
        </div>
      `;
      const btnCerrar = document.getElementById("cerrarSesion");
      if (btnCerrar) {
        btnCerrar.addEventListener("click", () => {
          if (confirm("¿Cerrar sesión?")) {
            logout();
          }
        });
      }
    }
  };

  if (isAuthenticated()) {
    const userEmail = localStorage.getItem("user_email");
    if (loginSection) loginSection.style.display = "none";
    mostrarUsuarioAutenticado(userEmail);
    
    // Configurar funcionalidad de la app
    configurarFuncionalidadNotas();
    configurarMapa();
    
  } else {
    // Configurar eventos de autenticación
    configurarEventosAuth();
  }
});

// 🔧 Función global para opciones avanzadas (llamada desde HTML)
function toggleOpcionesAvanzadas() {
  const panel = document.getElementById('opcionesAvanzadas');
  const btn = document.getElementById('toggleOpciones');
  if (panel && btn) {
    if (panel.style.display === 'none') {
      panel.style.display = 'block';
      btn.textContent = '− Ocultar opciones';
    } else {
      panel.style.display = 'none';
      btn.textContent = '+ Más opciones';
    }
  }
}
      