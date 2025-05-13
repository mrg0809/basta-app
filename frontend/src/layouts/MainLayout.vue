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
          Basta App ({{ authStore.isAuthenticated && authStore.initialCheckDone ? (authStore.userName || authStore.userEmail) : 'Invitado' }})
        </q-toolbar-title>

        <div class="q-gutter-sm row items-center no-wrap">
          <template v-if="authStore.isAuthenticated && authStore.initialCheckDone">
            <q-btn flat dense label="Crear Sala" :to="{ name: 'CreateRoom' }" icon="add_circle_outline" />
            <q-btn flat dense label="Unirse a Sala" :to="{ name: 'JoinRoom' }" icon="meeting_room" />
            <q-btn
              flat dense
              label="Cerrar Sesión"
              @click="handleSignOut"
              icon="logout"
              :loading="authStore.loading && !authStore.initialCheckDone" 
              :disable="authStore.loading && !authStore.initialCheckDone"
            />
          </template>
          
          <q-btn
            v-if="!authStore.isAuthenticated && authStore.initialCheckDone" flat
            label="Iniciar Sesión con Google"
            @click="handleSignInWithGoogle"
            icon="login"
            :loading="authStore.loading && !authStore.initialCheckDone"
            :disable="authStore.loading && !authStore.initialCheckDone"
          />

          <div v-if="!authStore.initialCheckDone || authStore.loading" class="q-mx-sm row items-center no-wrap">
              <q-spinner size="1.5em" class="q-mr-xs" />
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
          Menú Principal
        </q-item-label>
        
        <q-item clickable :to="{ name: 'GamePage' }" exact>
          <q-item-section avatar><q-icon name="sports_esports" /></q-item-section>
          <q-item-section><q-item-label>Juego BASTA</q-item-label></q-item-section>
        </q-item>

        <template v-if="authStore.isAuthenticated && authStore.initialCheckDone">
          <q-separator class="q-my-md" />
          <q-item-label header>Salas de Juego</q-item-label>
          
          <q-item clickable :to="{ name: 'CreateRoom' }">
            <q-item-section avatar><q-icon name="add_circle" /></q-item-section>
            <q-item-section><q-item-label>Crear Nueva Sala</q-item-label></q-item-section>
          </q-item>
          
          <q-item clickable :to="{ name: 'JoinRoom' }">
            <q-item-section avatar><q-icon name="group_add" /></q-item-section>
            <q-item-section><q-item-label>Unirse a Sala Existente</q-item-label></q-item-section>
          </q-item>
        </template>
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
import { useRouter } from 'vue-router';

const $q = useQuasar(); // $q se usa ahora
const authStore = useAuthStore();
const router = useRouter();
const leftDrawerOpen = ref(false);

const toggleLeftDrawer = () => {
  leftDrawerOpen.value = !leftDrawerOpen.value;
};

const handleSignInWithGoogle = async () => {
  // Esta guarda es útil para dar feedback inmediato en la UI si el botón
  // se clickea cuando ya está autenticado (aunque el v-if debería prevenirlo
  // una vez que el estado initialCheckDone es true).
  if (authStore.isAuthenticated && authStore.initialCheckDone) {
    $q.notify({ // <--- RESTAURAMOS EL USO DE $q.notify
      message: 'Ya has iniciado sesión.',
      color: 'info',
      icon: 'info_outline' // Un ícono apropiado
    });
    return;
  }
  // Solo llama a la acción del store si no estamos ya autenticados
  // (la acción del store también tiene una guarda, pero esta es para el feedback de UI)
  if (!authStore.isAuthenticated) {
    await authStore.signInWithGoogle();
  }
};

const handleSignOut = async () => {
  await authStore.signOut();
  router.replace('/');
};
</script>