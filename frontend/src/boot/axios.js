// src/boot/axios.js
import axios from 'axios'
import { useAuthStore } from 'src/stores/auth-store';

const api = axios.create({
   baseURL: 'http://localhost:8000/api/v1' 
});

// Request Interceptor
api.interceptors.request.use(config => {
  const authStore = useAuthStore(); // Obtener la instancia del store aquí
  const token = authStore.session?.access_token; // Acceder al token de la sesión

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

export default ({ app }) => {
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
}

export { api }