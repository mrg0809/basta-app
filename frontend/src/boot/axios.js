// src/boot/axios.js
import axios from 'axios'

// Podrías querer configurar tu baseURL aquí si ya sabes dónde estará tu API
// Por ejemplo:
// const api = axios.create({ baseURL: 'http://localhost:8000/api/v1' })
// Por ahora, solo crearemos una instancia simple. La configuraremos más adelante.
const api = axios.create({
   baseURL: 'http://localhost:8000/api/v1' 
});

export default ({ app }) => {
  // Para uso dentro de archivos Vue (Options API), a través de this.$axios y this.$api
  // Esto es opcional si principalmente usarás la instancia importada.
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api // Haciendo nuestra instancia configurada disponible
}

// Exporta la instancia `api` para que puedas importarla directamente en tus archivos JS/TS (ej. en stores de Pinia)
export { api }