# app.py

# app.py

import streamlit as st
import requests
from datetime import datetime
import streamlit.components.v1 as components
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from streamlit_javascript import st_javascript

load_dotenv()

st.set_page_config(page_title="Notas a Uno Mismo", layout="centered")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("📝 Notas a Uno Mismo")
tabs = st.tabs(["➕ Nueva nota", "📚 Historial", "🔍 Buscar nota"])

# Estado para ubicación automática
if "geo_lat" not in st.session_state:
    st.session_state["geo_lat"] = None
if "geo_lon" not in st.session_state:
    st.session_state["geo_lon"] = None

# Componente HTML para capturar ubicación del navegador
components.html("""
<script>
const sendLocation = (position) => {
    const coords = {
        lat: position.coords.latitude,
        lon: position.coords.longitude
    };
    window.parent.postMessage({type: "geo", payload: coords}, "*");
};

const requestLocation = () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(sendLocation, (err) => {
            window.parent.postMessage({type: "geo", payload: {error: err.message}}, "*");
        });
    } else {
        window.parent.postMessage({type: "geo", payload: {error: "Geolocation not supported"}}, "*");
    }
};

window.addEventListener("DOMContentLoaded", requestLocation);
</script>
""", height=0)

# === TAB 1: NUEVA NOTA ===
with tabs[0]:
    st.markdown("Escribí lo que estás pensando o sintiendo en este momento. Solo con eso, el sistema intentará completar todo lo demás automáticamente.")

    with st.form("nota_form"):
        user_email = st.text_input("Tu email", value="alejandro@ejemplo.com")
        texto = st.text_area("Tu nota", height=200)
        emocion = st.text_input("¿Cómo te sentís? (opcional)", placeholder="Feliz, Triste...")
        tags = st.text_input("Tags (opcional, separados por coma)", placeholder="trabajo, idea, personal")
        categoria = st.text_input("Categoría (opcional)", placeholder="Reflexión, Trabajo, Salud...")
        ubicacion_textual = st.text_input("¿Dónde estás? (opcional)", placeholder="Palermo, Parque Centenario...")
        lat = st.text_input("Latitud (opcional)", placeholder="Se detectará automáticamente")
        lon = st.text_input("Longitud (opcional)", placeholder="Se detectará automáticamente")


        # Mostrar coordenadas detectadas desde localStorage si no se completaron manualmente
        components.html("""
            <script>
            navigator.geolocation.getCurrentPosition(function(position) {
                localStorage.setItem('geo_lat', position.coords.latitude);
                localStorage.setItem('geo_lon', position.coords.longitude);
                window.parent.postMessage({
                   type: 'streamlit:setComponentValue',
                   value: {
                      latitude: position.coords.latitude,
                      longitude: position.coords.longitude
            });
            </script>
        """, height=0)

        coords = st_javascript("""
            new Promise((resolve) => {
                setTimeout(() => {
                    resolve(JSON.stringify({
                        lat: localStorage.getItem('geo_lat'),
                        lon: localStorage.getItem('geo_lon')
                    }));
                 }, 500);
            })
        """)
        if coords:
            try:
                coords_json = json.loads(coords)
                st.session_state.geo_lat = coords_json.get("lat")
                st.session_state.geo_lon = coords_json.get("lon")
            except:
                st.warning("No se pudieron leer las coordenadas del navegador.")

        submit = st.form_submit_button("💾 Guardar Nota")

        st.markdown(f"📡 Coordenadas detectadas (session): lat **{st.session_state.get('geo_lat')}**, lon **{st.session_state.get('geo_lon')}**")

    if submit:
        default_lat = 49.2827   # Vancouver BC
        default_lon = -123.1207

        lat_origen = ""
        try:
            lat_final = float(lat.strip()) if lat.strip() else float(st.session_state.get("geo_lat"))
            lat_origen = "manual" if lat.strip() else "geolocalización"
        except:
            lat_final = default_lat
            lat_origen = "por defecto (Vancouver)"

        try:
            lon_final = float(lon.strip()) if lon.strip() else float(st.session_state.get("geo_lon"))
        except:
            lon_final = default_lon

        st.markdown(f"📍 Coordenadas utilizadas: **lat {lat_final}, lon {lon_final}** ({lat_origen})")

        emocion_out, categoria_out, tags_out, ubicacion_out = None, None, [], None

        if not emocion or not categoria or not tags or not ubicacion_textual:
            try:
                prompt = f"""
Dado el siguiente texto:
{texto}
1. ¿Qué emoción transmite el texto? (1 palabra, por ejemplo: Feliz, Triste)
2. ¿Qué categoría podría tener este texto? (ej: Trabajo, Salud, Reflexión, Personal)
3. Lista de 1 a 5 tags relevantes, separados por coma.
4. ¿Qué ubicación textual se deduce si hay alguna? (por ejemplo, Palermo, oficina, casa)
"""
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                respuesta = completion.choices[0].message.content.strip().split("\n")
                if len(respuesta) >= 4:
                    emocion_out = respuesta[0].split(":")[-1].strip()
                    categoria_out = respuesta[1].split(":")[-1].strip()
                    tags_out = [t.strip() for t in respuesta[2].split(":")[-1].split(",")]
                    ubicacion_out = respuesta[3].split(":")[-1].strip()
            except Exception as e:
                st.warning(f"No se pudo completar automáticamente: {e}")

        payload = {
            "user_email": user_email,
            "texto": texto,
            "emocion": emocion if emocion.strip() else emocion_out,
            "tags": [tag.strip() for tag in tags.split(",") if tag.strip()] if tags.strip() else tags_out or [],
            "categoria": categoria if categoria.strip() else categoria_out,
            "ubicacion_textual": ubicacion_textual if ubicacion_textual.strip() else ubicacion_out,
            "latitud": lat_final,
            "longitud": lon_final,
        }

        st.subheader("Payload a enviar")
        st.code(payload, language="json")

        try:
            response = requests.post("https://notasia.1963.com.ar/guardar-nota", json=payload)
            if response.status_code == 200:
                st.success("✅ Nota guardada correctamente.")
            else:
                st.error(f"❌ Error al guardar la nota: {response.status_code}")
                try:
                    st.json(response.json())
                except Exception:
                    st.write(response.text)
        except Exception as e:
            st.error(f"⚠️ Error de conexión: {e}")

# === TAB 2: HISTORIAL ===
with tabs[1]:
    st.subheader("📚 Historial de Notas")
    email_hist = st.text_input("Ingresá tu email para ver tus notas", key="hist_email")
    if email_hist:
        try:
            res = requests.get(f"https://notasia.1963.com.ar/notas-por-email?email={email_hist}")
            if res.status_code == 200:
                notas = res.json().get("notas", [])
                if notas:
                    for nota in notas:
                        with st.expander(f"🕒 {nota['fecha']} {nota['hora']} - {nota['emocion'] or 'Sin emoción'}"):
                            st.markdown(f"**Texto:** {nota['texto']}")
                            st.markdown(f"**Categoría:** {nota['categoria'] or 'Sin categoría'}")
                            st.markdown(f"**Tags:** {nota['tags'] or 'Sin tags'}")
                            st.markdown(f"**Ubicación:** {nota['ubicacion_textual'] or 'No especificada'}")
                            st.markdown(f"**Lat/Lon:** {nota['latitud']}, {nota['longitud']}")
                else:
                    st.info("No se encontraron notas para este email.")
            else:
                st.error(f"Error al consultar el historial: {res.status_code}")
        except Exception as e:
            st.error(f"Error en la conexión: {e}")

# === TAB 3: BÚSQUEDA ===
with tabs[2]:
    st.subheader("🔍 Buscar Notas por Similaridad")
    email_busqueda = st.text_input("Tu email para buscar", key="search_email")
    texto_busqueda = st.text_area("Texto de búsqueda")
    k = st.slider("Cantidad de resultados (k)", min_value=1, max_value=20, value=5)

    if st.button("🔎 Buscar"):
        if not email_busqueda or not texto_busqueda:
            st.warning("Por favor ingresá tu email y el texto de búsqueda.")
        else:
            try:
                res = requests.get(f"https://notasia.1963.com.ar/buscar-notas?email={email_busqueda}&texto={texto_busqueda}&k={k}")
                if res.status_code == 200:
                    resultados = res.json().get("resultados", [])
                    if resultados:
                        resumen_prompt = f"""
Tenés la siguiente lista de notas tomadas por un usuario. Cada nota tiene campos como fecha, hora, texto, emoción, etc.

Notas:
{json.dumps(resultados, indent=2, ensure_ascii=False)}

Pregunta del usuario: "{texto_busqueda}"

Respondé en una o dos frases con la mejor respuesta directa posible, basada exclusivamente en el contenido de las notas anteriores.
Si se puede inferir una persona, un lugar, o una acción concreta, respondé de forma clara y directa.
"""
                        try:
                            completion = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": resumen_prompt}]
                            )
                            respuesta_natural = completion.choices[0].message.content.strip()
                            st.info(f"🧠 GPT sugiere: {respuesta_natural}")
                        except Exception as e:
                            st.warning(f"No se pudo interpretar los resultados: {e}")

                        st.success(f"Se encontraron {len(resultados)} resultados:")
                        for r in resultados:
                            with st.expander(f"📌 {r['fecha']} {r['hora']} - {r['emocion'] or 'Sin emoción'}"):
                                st.markdown(f"**Texto:** {r['texto']}")
                                st.markdown(f"**Categoría:** {r['categoria'] or 'Sin categoría'}")
                                st.markdown(f"**Tags:** {r['tags'] or 'Sin tags'}")
                                st.markdown(f"**Ubicación:** {r['ubicacion_textual'] or 'No especificada'}")
                    else:
                        st.info("No se encontraron coincidencias relevantes.")
                else:
                    st.error(f"Error: {res.status_code}")
                    st.write(res.text)
            except Exception as e:
                st.error(f"Error en la conexión: {e}")
