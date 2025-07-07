# 📝 Notas a Uno Mismo

**Notas a Uno Mismo** es una aplicación web que permite a los usuarios registrar notas personales, enriquecidas automáticamente con metadatos como emociones, categorías, etiquetas y ubicación. Las notas pueden buscarse semánticamente gracias a embeddings generados con OpenAI y almacenados en Pinecone.

---

## 🚀 Funcionalidades principales

- Registro de notas personales con fecha, hora y ubicación.
- Enriquecimiento automático de las notas usando GPT-3.5 (emoción, categoría, etiquetas, ubicación textual).
- Búsqueda semántica de notas mediante embeddings y Pinecone.
- Visualización de notas en un mapa interactivo.
- Historial de notas por usuario.
- Análisis de fechas desde texto en lenguaje natural (por ejemplo: "ayer", "entre el 10 y el 15 de junio").
- Interfaz web simple y funcional.

---

## 🧠 Tecnologías utilizadas

- **Backend**: FastAPI
- **Frontend**: HTML + JavaScript
- **IA**: OpenAI GPT-3.5 y GPT-4 para enriquecimiento y resumen
- **Base vectorial**: Pinecone
- **Base de datos**: MySQL
- **Geolocalización**: API del navegador + OpenAI
- **Embeddings**: `text-embedding-3-small`

---

## 📂 Estructura del proyecto
