<template>
    <q-page padding>
      <div class="row justify-center">
        <div class="col-12 col-md-8 col-lg-6">
          <q-card class="q-mt-md">
            <q-card-section class="bg-primary text-white">
              <div class="text-h6">Crear Nueva Sala de Juego</div>
            </q-card-section>
  
            <q-separator />
  
            <q-card-section>
              <q-form @submit.prevent="handleCreateRoom" class="q-gutter-md">
                <q-select
                  filled
                  v-model="selectedThemeId"
                  :options="themeOptions"
                  label="Selecciona una Temática *"
                  emit-value
                  map-options
                  lazy-rules
                  :rules="[val => !!val || 'Por favor, selecciona una temática']"
                  :loading="gameStore.isLoadingThemes" 
                  :disable="gameStore.isLoadingThemes"
                >
                  <template v-if="gameStore.isLoadingThemes" v-slot:prepend>
                    <q-spinner color="primary" />
                  </template>
                </q-select>
  
                <q-input
                  filled
                  v-model.number="maxPlayersInput"
                  type="number"
                  label="Número Máximo de Jugadores (2-16)"
                  hint="Entre 2 y 16 jugadores. Por defecto: 8."
                  lazy-rules
                  :rules="[
                    val => (val === null || val === '' || (val >= 2 && val <= 16)) || 'Debe ser un número entre 2 y 16'
                  ]"
                />
  
                <div v-if="roomStore.roomError" class="text-negative q-mb-md">
                  Error: {{ roomStore.roomError }}
                </div>
  
                <div>
                  <q-btn
                    label="Crear Sala"
                    type="submit"
                    color="primary"
                    class="full-width"
                    :loading="roomStore.isLoadingRoom"
                    :disable="!selectedThemeId || roomStore.isLoadingRoom"
                  />
                </div>
              </q-form>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </q-page>
  </template>
  
  <script setup>
  import { ref, onMounted, computed } from 'vue';
  import { useRouter } from 'vue-router';
  import { useGameStore } from 'stores/game-store';   // Para las temáticas
  import { useRoomStore } from 'stores/room-store';   // Para crear la sala
  import { Notify } from 'quasar'; // Para notificaciones directas si es necesario
  
  const router = useRouter();
  const gameStore = useGameStore();
  const roomStore = useRoomStore();
  
  const selectedThemeId = ref(null);
  const maxPlayersInput = ref(null); // null para que el backend use su default si no se ingresa
  
  // Opciones para el q-select de temáticas
  const themeOptions = computed(() => {
    if (!gameStore.themes || gameStore.themes.length === 0) {
      return [{ label: 'Cargando temáticas...', value: null, disable: true }];
    }
    return gameStore.themes.map(theme => ({
      label: theme.name,
      value: theme.id
    }));
  });
  
  onMounted(async () => {
    // Limpiar errores previos de sala al entrar a la página
    roomStore.roomError = null; 
    
    // Cargar temáticas si no están ya en el gameStore
    // Asumimos que gameStore podría tener su propio flag de carga, ej. gameStore.isLoadingThemes
    if (!gameStore.themes || gameStore.themes.length === 0) {
      // gameStore podría tener un isLoadingThemes que usamos en el template
      // gameStore.isLoadingThemes = true; // Si necesitas manejarlo manualmente
      await gameStore.fetchThemes();
      // gameStore.isLoadingThemes = false;
    }
  });
  
  const handleCreateRoom = async () => {
    if (!selectedThemeId.value) {
      Notify.create({ type: 'negative', message: 'Debes seleccionar una temática.' });
      return;
    }
  
    // Validar maxPlayers si se ingresó
    if (maxPlayersInput.value !== null && maxPlayersInput.value !== '' && (maxPlayersInput.value < 2 || maxPlayersInput.value > 16)) {
        Notify.create({ type: 'negative', message: 'El número máximo de jugadores debe ser entre 2 y 16.' });
        return;
    }
  
    const roomDetails = {
      themeId: selectedThemeId.value,
      // Si maxPlayersInput es null o string vacío, no lo enviamos para que el backend use su default.
      // El backend ya tiene un default de 8, y el modelo Pydantic también.
      // Si el input es 0, también sería inválido según las reglas, pero el backend lo validaría.
      // Lo mejor es enviar null si el usuario no escribe nada o borra el campo.
      maxPlayers: (maxPlayersInput.value === null || maxPlayersInput.value === '') ? undefined : Number(maxPlayersInput.value)
    };
    
    // console.log('Creating room with details:', roomDetails);
  
    const newRoomData = await roomStore.createRoom(roomDetails);
  
    if (newRoomData && newRoomData.id) {
      // Redirigir al lobby de la sala recién creada
      router.push({ name: 'RoomLobby', params: { roomId: newRoomData.id } });
    } else {
      // El error ya debería haberse mostrado a través de roomStore.roomError o una notificación desde el store.
      // Aquí podríamos añadir una notificación genérica si la del store no fue suficiente.
      // Notify.create({ type: 'negative', message: roomStore.roomError || 'No se pudo crear la sala.' });
    }
  };
  </script>
  
  <style scoped>
  .q-card {
    max-width: 500px; /* O el ancho que prefieras */
  }
  </style>