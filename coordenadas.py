import streamlit as st
import streamlit.components.v1 as components
import json
import time

def get_geolocation():
    """
    Obtiene la geolocalización del usuario de forma más robusta
    """
    # Componente HTML mejorado con mejor manejo de errores
    location_component = components.html("""
        <div id="location-status" style="padding: 10px; font-family: Arial, sans-serif;">
            <p id="status-text">🔍 Solicitando acceso a ubicación...</p>
        </div>
        
        <script>
        function updateStatus(message, isError = false) {
            const statusElement = document.getElementById('status-text');
            statusElement.textContent = message;
            statusElement.style.color = isError ? 'red' : 'green';
        }
        
        function sendLocationToStreamlit(lat, lon) {
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {
                    latitude: lat,
                    longitude: lon,
                    timestamp: new Date().toISOString(),
                    status: 'success'
                }
            }, '*');
        }
        
        function sendErrorToStreamlit(error) {
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {
                    latitude: null,
                    longitude: null,
                    timestamp: new Date().toISOString(),
                    status: 'error',
                    error: error
                }
            }, '*');
        }
        
        // Verificar si geolocalización está disponible
        if (!navigator.geolocation) {
            updateStatus('❌ Geolocalización no disponible en este navegador', true);
            sendErrorToStreamlit('Geolocation not supported');
        } else {
            // Configurar opciones de geolocalización
            const options = {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            };
            
            // Función de éxito
            function success(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const accuracy = position.coords.accuracy;
                
                updateStatus(`✅ Ubicación obtenida (precisión: ${Math.round(accuracy)}m)`);
                sendLocationToStreamlit(lat, lon);
            }
            
            // Función de error
            function error(err) {
                let message = '❌ Error: ';
                switch(err.code) {
                    case err.PERMISSION_DENIED:
                        message += 'Permiso denegado por el usuario';
                        break;
                    case err.POSITION_UNAVAILABLE:
                        message += 'Ubicación no disponible';
                        break;
                    case err.TIMEOUT:
                        message += 'Tiempo de espera agotado';
                        break;
                    default:
                        message += 'Error desconocido';
                        break;
                }
                updateStatus(message, true);
                sendErrorToStreamlit(message);
            }
            
            // Solicitar ubicación
            navigator.geolocation.getCurrentPosition(success, error, options);
        }
        </script>
    """, height=80)
    
    return location_component

# Función principal para usar en tu aplicación
def main():
    st.title("📍 Detector de Geolocalización")
    
    # Inicializar variables de sesión
    if 'location_data' not in st.session_state:
        st.session_state.location_data = None
    
    # Crear columnas para mejor layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Obtener Ubicación")
        
        # Botón para obtener ubicación
        if st.button("🎯 Obtener mi ubicación", type="primary"):
            st.session_state.location_requested = True
        
        # Solo mostrar el componente si se solicitó la ubicación
        if st.session_state.get('location_requested', False):
            location_data = get_geolocation()
            
            # Actualizar datos de ubicación si se recibieron
            if location_data:
                st.session_state.location_data = location_data
                st.session_state.location_requested = False
                st.rerun()
    
    with col2:
        st.subheader("Estado")
        
        # Mostrar información de ubicación
        if st.session_state.location_data:
            data = st.session_state.location_data
            
            if data.get('status') == 'success':
                st.success("✅ Ubicación obtenida")
                
                # Mostrar coordenadas
                lat = data.get('latitude')
                lon = data.get('longitude')
                
                if lat and lon:
                    st.metric("Latitud", f"{float(lat):.6f}")
                    st.metric("Longitud", f"{float(lon):.6f}")
                    
                    # Timestamp
                    if data.get('timestamp'):
                        st.caption(f"Obtenida: {data['timestamp']}")
                    
                    # Botón para limpiar
                    if st.button("🗑️ Limpiar"):
                        st.session_state.location_data = None
                        st.rerun()
                        
            elif data.get('status') == 'error':
                st.error("❌ Error al obtener ubicación")
                st.write(data.get('error', 'Error desconocido'))
        else:
            st.info("📍 No hay datos de ubicación")
    
    # Sección adicional: Mostrar en mapa (opcional)
    if st.session_state.location_data and st.session_state.location_data.get('status') == 'success':
        st.subheader("🗺️ Ubicación en el Mapa")
        
        lat = float(st.session_state.location_data.get('latitude'))
        lon = float(st.session_state.location_data.get('longitude'))
        
        # Crear DataFrame para el mapa
        import pandas as pd
        df = pd.DataFrame({
            'lat': [lat],
            'lon': [lon]
        })
        
        # Mostrar mapa
        st.map(df, zoom=15)
        
        # Información adicional
        with st.expander("ℹ️ Información técnica"):
            st.json({
                "latitude": lat,
                "longitude": lon,
                "timestamp": st.session_state.location_data.get('timestamp'),
                "coordinates_string": f"{lat},{lon}"
            })

# Ejemplo de uso en un formulario
def location_form_example():
    st.subheader("📝 Formulario con Geolocalización")
    
    with st.form("location_form"):
        st.write("Completa el formulario y obtén tu ubicación:")
        
        # Campos del formulario
        nombre = st.text_input("Nombre")
        nota = st.text_area("Nota")
        
        # Botón para obtener ubicación dentro del formulario
        get_location = st.form_submit_button("📍 Obtener Ubicación")
        
        if get_location:
            # Aquí usarías el componente de geolocalización
            st.info("Solicitando ubicación...")
            
        # Mostrar coordenadas si están disponibles
        if st.session_state.get('location_data'):
            data = st.session_state.location_data
            if data.get('status') == 'success':
                lat = data.get('latitude')
                lon = data.get('longitude')
                st.success(f"📡 Coordenadas: {lat}, {lon}")
        
        # Botón para guardar
        submit = st.form_submit_button("💾 Guardar Nota")
        
        if submit:
            if st.session_state.get('location_data'):
                st.success("✅ Nota guardada con ubicación!")
            else:
                st.warning("⚠️ Nota guardada sin ubicación")

if __name__ == "__main__":
    main()
    st.divider()
    location_form_example()
