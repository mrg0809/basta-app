// src/boot/pinia.js
import { createPinia } from 'pinia'

// "async" es opcional; úsalo si necesitas esperar algo (ej. una promesa)
export default async ({ app }) => {
  const pinia = createPinia()
  app.use(pinia)
  // Puedes añadir plugins de Pinia aquí si los necesitas
  // por ejemplo: pinia.use(MyPiniaPlugin)
}