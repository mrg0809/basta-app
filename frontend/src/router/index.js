// src/router/index.js
import { route } from 'quasar/wrappers';
import {
  createRouter,
  createMemoryHistory,
  createWebHistory,
  // createWebHashHistory // Ya no se usa si cambiaste a history mode
} from 'vue-router';
import routes from './routes';
import { useAuthStore } from 'stores/auth-store'; // Importa tu authStore

export default route(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : createWebHistory; // Asumiendo que ya cambiaste a history mode

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(process.env.VUE_ROUTER_BASE),
  });

  // --- GUARDA DE NAVEGACIÓN ---
  Router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore(); // Obtener instancia dentro de la guarda

    // Asegurarse de que la comprobación inicial de sesión se haya hecho
    // o que el store esté listo, especialmente si `initialCheckDone` está en el store.
    // Si initialCheckDone no está en true, podríamos estar en medio de fetchCurrentSession.
    // Esperar a que initialCheckDone sea true podría ser una opción, o comprobar si ya está listo.

    // Intenta cargar la sesión si aún no se ha comprobado y no estamos en una ruta pública clave
    // Esto es para manejar el caso de recarga de página en una ruta protegida.
    if (!authStore.initialCheckDone && to.meta.requiresAuth) {
        // console.log('Router Guard: Initial check not done, fetching session for protected route...');
        await authStore.fetchCurrentSession(); // Asegura que la sesión se intente cargar
    }

    const requiresAuth = to.meta.requiresAuth;
    const isAuthenticated = authStore.isAuthenticated; // Ya debería estar actualizado por fetchCurrentSession

    // console.log(`Router Guard: Navigating to ${to.path}, requiresAuth: ${requiresAuth}, isAuthenticated: ${isAuthenticated}, initialCheckDone: ${authStore.initialCheckDone}`);

    if (requiresAuth && !isAuthenticated && authStore.initialCheckDone) {
      // Si la ruta requiere autenticación, el usuario no está autenticado,
      // y la comprobación inicial ya se hizo (para no redirigir prematuramente).
      // Redirigir a una página de inicio/login.
      // Si tienes una página de login dedicada: next({ name: 'Login' });
      // Si tu login está en la página principal:
      next({ path: '/' }); // Redirige a la raíz donde está el botón de login
    } else {
      // Si no requiere autenticación, o si la requiere y está autenticado, o si initialCheckDone es false (dejar que App.vue maneje)
      next();
    }
  });
  // -------------------------

  return Router;
});