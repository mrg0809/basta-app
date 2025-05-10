<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          Basta App ({{ authStore.isAuthenticated ? (authStore.userName || authStore.userEmail) : 'Invitado' }})
        </q-toolbar-title>

        <div>
          <q-btn
            v-if="!authStore.isAuthenticated && authStore.initialCheckDone" flat
            label="Iniciar Sesión con Google"
            @click="handleSignInWithGoogle"
            icon="login"
            :loading="authStore.loading"
            :disable="authStore.loading"
          />
          <q-btn
            v-if="authStore.isAuthenticated && authStore.initialCheckDone" flat
            label="Cerrar Sesión"
            @click="handleSignOut"
            icon="logout"
            :loading="authStore.loading"
            :disable="authStore.loading"
          />
          <div v-if="!authStore.initialCheckDone || authStore.loading" class="q-mx-sm">
              <q-spinner size="xs" />
          </div>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
    >
      <q-list>
        <q-item-label header>
          Menú
        </q-item-label>
        <q-item clickable to="/" exact>
          <q-item-section avatar><q-icon name="home" /></q-item-section>
          <q-item-section><q-item-label>Inicio (Juego)</q-item-label></q-item-section>
        </q-item>
        </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from 'stores/auth-store';
import { useQuasar } from 'quasar';

const $q = useQuasar();
const authStore = useAuthStore();
const leftDrawerOpen = ref(false);

const toggleLeftDrawer = () => {
  leftDrawerOpen.value = !leftDrawerOpen.value;
};

const handleSignInWithGoogle = async () => {
  if (authStore.isAuthenticated) { // Doble chequeo
    $q.notify.create({ message: 'Ya has iniciado sesión.', color: 'info' });
    return;
  }
  await authStore.signInWithGoogle();
  // La redirección a Google ocurre dentro de la acción del store.
  // onAuthStateChange manejará la actualización del estado cuando el usuario regrese.
};

const handleSignOut = async () => {
  await authStore.signOut();
  // onAuthStateChange manejará la actualización del estado.
  // Podrías redirigir aquí si es necesario, ej. a una página de inicio pública.
  // import { useRouter } from 'vue-router';
  // const router = useRouter();
  // router.push('/');
};
</script>