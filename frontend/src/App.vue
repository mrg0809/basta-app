// src/App.vue
<template>
  <router-view />
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { useAuthStore } from 'stores/auth-store';
import { useRouter, useRoute } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

onMounted(async () => {
  console.log('App.vue onMounted: Current window.location.hash:', window.location.hash);

  // 1. Configura el listener PRIMERO.
  //    Esto es crucial para que esté listo para el evento SIGNED_IN
  //    que el cliente Supabase debería disparar si procesa el hash de la URL.
  authStore.initializeAuthListener();

  // 2. Intenta obtener la sesión actual.
  //    Si el cliente Supabase ya procesó el hash de la URL (debido a detectSessionInUrl: true
  //    en su inicialización), getSession() podría devolver la nueva sesión,
  //    o onAuthStateChange ya se habrá disparado con SIGNED_IN.
  //    Si no hay hash, intentará cargar desde localStorage.
  await authStore.fetchCurrentSession();

  // Log para verificar el estado después de la inicialización
  console.log(`App.vue onMounted: Post-init: isAuthenticated: ${authStore.isAuthenticated}, initialCheckDone: ${authStore.initialCheckDone}`);
  if (!authStore.isAuthenticated && window.location.hash.includes('access_token')) {
      console.error("App.vue onMounted: Fallo crítico - Hay un hash de OAuth pero el usuario no está autenticado. El cliente Supabase no procesó el hash.");
  }
});

// Watcher para limpiar la URL DESPUÉS de que justSignedIn se establece por onAuthStateChange
watch(() => authStore.justSignedIn, (isNewlySignedIn) => {
  if (isNewlySignedIn) {
    const currentHash = route.hash; // Obtener el hash actual
    console.log('App.vue Watcher (justSignedIn): Es true. Hash actual:', currentHash);
    if (currentHash.includes('access_token') || currentHash.includes('error_description')) {
      console.log('App.vue Watcher (justSignedIn): Limpiando hash OAuth y redirigiendo a /');
      router.replace({ path: '/', hash: '' });
    }
    authStore.clearJustSignedInFlag();
  }
});

// Watcher para cierre de sesión
watch(() => authStore.isAuthenticated, (newIsAuthenticated, oldIsAuthenticated) => {
  if (authStore.initialCheckDone && !newIsAuthenticated && oldIsAuthenticated) {
    console.log('App.vue Watcher (isAuthenticated): Usuario ha cerrado sesión.');
    if (route.meta.requiresAuth) {
        // router.replace({ name: 'Login' }); // Si tienes una ruta de Login con nombre
        router.replace('/'); // O simplemente a la raíz
    }
  }
});
</script>