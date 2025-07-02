// app.js

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

document.addEventListener("DOMContentLoaded", () => {
  const emailGuardado = localStorage.getItem("user_email");
  const sesionInfo = document.getElementById("sesionInfo");
  const loginSection = document.getElementById("loginSection");

  const mostrarEmail = (email) => {
    sesionInfo.innerHTML = `
      <div>
        <small>Sesión iniciada con:</small><br>
        <strong>${email}</strong>
        <button class="btn btn-sm btn-outline-danger ms-2" id="cerrarSesion">🔓 Cerrar sesión</button>
      </div>
    `;
    document.getElementById("cerrarSesion").addEventListener("click", () => {
      localStorage.removeItem("user_email");
      location.reload();
    });
  };

  if (emailGuardado) {
    loginSection.style.display = "none";
    mostrarEmail(emailGuardado);
  } else {
    document.getElementById("iniciarSesion").addEventListener("click", () => {
      const email = document.getElementById("loginEmail").value.trim();
      if (email) {
        localStorage.setItem("user_email", email);
        location.reload();
      }
    });
    return;
  }

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
    document.getElementById("geo-status").textContent = "No se pudo obtener ubicación.";
  });

  const notaForm = document.getElementById("notaForm");
  if (notaForm) {
    notaForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fechaManualInput = document.getElementById("fechaManual");
console.log("⏱ Fecha manual DOM:", fechaManualInput);
console.log("📤 Valor capturado:", fechaManualInput?.value);
const payload = {
        user_email: emailGuardado,
        texto: document.getElementById("texto").value.trim(),
        emocion: document.getElementById("emocion").value.trim() || undefined,
        tags: document.getElementById("tags").value.trim().split(",").filter(tag => tag),
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
          document.getElementById("resultado").textContent = "✅ Nota guardada con éxito.";
          notaForm.reset();
        } else {
          document.getElementById("resultado").textContent = "❌ Error al guardar la nota.";
        }
      } catch (err) {
        document.getElementById("resultado").textContent = "⚠️ Error al conectar con el servidor.";
      }
    });
  }

  document.getElementById("cargarHistorial").addEventListener("click", async () => {
    const contenedor = document.getElementById("resultadoHistorial");
    contenedor.innerHTML = "⏳ Cargando...";
    try {
      const res = await fetch(`https://notasia.1963.com.ar/notas-por-email?email=${encodeURIComponent(emailGuardado)}`);
      const data = await res.json();
      contenedor.innerHTML = "";
      if (data.notas && data.notas.length > 0) {
        data.notas.forEach(nota => {
          const div = document.createElement("div");
          div.className = "border p-2 mb-2";
          const horaLegible = formatearHora(nota.hora);
          const titulo = nota.titulo || nota.texto?.slice(0, 40) || "(sin título)";
          div.innerHTML = `<strong>${titulo}</strong><br><small>${nota.fecha} ${horaLegible}</small><br>${nota.texto}`;
          contenedor.appendChild(div);
        });
      } else {
        contenedor.textContent = "📭 No se encontraron notas.";
      }
    } catch {
      contenedor.textContent = "⚠️ Error al obtener historial.";
    }
  });

  document.getElementById("buscarNotas").addEventListener("click", async () => {
    const texto = document.getElementById("textoBuscar").value.trim();
    const contenedor = document.getElementById("resultadoBusqueda");
    const offsetMin = new Date().getTimezoneOffset();
    const offsetHoras = -offsetMin / 60;

    contenedor.innerHTML = "🔎 Buscando...";
    try {
      const res = await fetch(
        `https://notasia.1963.com.ar/buscar-notas?email=${encodeURIComponent(emailGuardado)}&texto=${encodeURIComponent(texto)}&offset=${offsetHoras}`
      );
      const data = await res.json();
      contenedor.innerHTML = "";
      if (data.resumen) {
        const resumen = document.createElement("div");
        resumen.className = "alert alert-info";
        resumen.innerHTML = `<strong>🧠 GPT dice:</strong><br>${data.resumen}`;
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

  async function cargarMapa() {
    const contenedor = document.getElementById("mapaContainer");
    contenedor.innerHTML = "⏳ Cargando mapa...";

    try {
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

  document.querySelector('button[data-bs-target="#mapa"]').addEventListener('shown.bs.tab', () => {
    if (!mapaYaCargado) {
      cargarMapa();
      mapaYaCargado = true;
    }
  });

  document.getElementById("refrescarMapa").addEventListener("click", () => {
    cargarMapa();
  });
});