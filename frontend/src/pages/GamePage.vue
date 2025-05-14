<template>
  <q-page padding>
    <div v-if="!roomStore.currentRoom || !gameStore.isGameSetupCompleteForRoom" class="fixed-center text-center">
      <q-spinner color="primary" size="3em" v-if="isLoadingPageData" />
      <div v-if="isLoadingPageData" class="q-mt-md">Preparando juego de sala...</div>
      <div v-if="!isLoadingPageData && !pageError" class="text-h6">
        No se pudo cargar la información del juego de la sala.
        <q-btn flat label="Volver al Inicio" to="/" color="primary" />
      </div>
      <div v-if="pageError" class="text-negative">
        Error: {{ pageError }}
        <q-btn flat label="Volver al Inicio" to="/" color="primary" />
      </div>
    </div>

    <div v-else class="q-pa-md">
      <div class="text-h4 q-mb-md text-center">
        BASTA - {{ gameStore.currentThemeForRoom?.name || '...' }}
      </div>

      <div class="row q-mb-md items-center justify-between">
        <div class="text-h5">Letra: <span class="text-primary text-weight-bolder">{{ roomStore.currentRoom.current_letter }}</span></div>
        <div>Ronda: {{ roomStore.currentRoom.current_round_number }}</div>
        </div>

      <q-form @submit.prevent="handlePlayerSaysBasta">
        <div v-for="category in gameStore.currentCategories" :key="category.id" class="q-mb-sm">
          <q-input
            filled
            :model-value="answers[category.id]"
            @update:model-value="value => updateAnswer(category.id, value)"
            :label="category.name"
            :disable="gameIsOverForPlayer" 
            bottom-slots
            dense
          >
            </q-input>
        </div>

        <q-btn
          label="¡BASTA!"
          type="submit"
          color="negative"
          class="q-mt-md full-width"
          :disable="gameIsOverForPlayer"
          :loading="isSubmittingBasta"
        />
      </q-form>

      <div v-if="gameIsOverForPlayer && !showingRoundResults" class="q-mt-lg text-center">
        <div v-if="roomStore.currentRoom?.status === 'scoring'">
          <div class="text-h5">Ronda Terminada</div>
          <div class="text-subtitle1">Calculando puntajes...</div>
          <q-linear-progress indeterminate color="secondary" class="q-my-md" />
        </div>
        <div v-else> <div class="text-h5">¡BASTA!</div>
          <div class="text-subtitle1">Esperando a los demás jugadores...</div>
          <q-linear-progress indeterminate color="primary" class="q-my-md" />
        </div>
      </div>

      <div v-if="countdownSeconds > 0 && !gameIsOverForPlayer" class="text-center q-my-md">
        <q-chip square color="orange" text-color="white" icon="campaign">
          ¡{{ bastaCallerNickname }} dijo BASTA! Quedan... BASTA {{ countdownSeconds }}
        </q-chip>
      </div>
      <div v-if="countdownSeconds > 0 && gameIsOverForPlayer && authStore.userId === roomStore.currentRoom?.current_round_basta_caller_id" class="text-center q-my-md">
        <q-chip square color="green" text-color="white" icon="flag">
          ¡Dijiste BASTA! Esperando a los demás ({{countdownSeconds }}s)...
        </q-chip>
      </div>
      
      <div v-if="showingRoundResults">
          </div>

    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useRoomStore } from 'stores/room-store';
import { useGameStore } from 'stores/game-store';
import { useAuthStore } from 'stores/auth-store';
import { useQuasar } from 'quasar';
import { supabase } from 'boot/supabase-client';

const $q = useQuasar();
const router = useRouter();
const roomStore = useRoomStore();
const gameStore = useGameStore();
const authStore = useAuthStore();

const answers = ref({});
const isLoadingPageData = ref(true);
const pageError = ref(null);
const gameIsOverForPlayer = ref(false);
const isSubmittingBasta = ref(false);
const showingRoundResults = ref(false);

const countdownSeconds = ref(0);
const countdownInterval = ref(null);
const bastaCallerNickname = ref('');

let gameRoomUpdateChannel = null;

// COMPUTEDS que SÍ se usan o podrían usarse internamente o en el template
const currentRoomDetails = computed(() => roomStore.currentRoom);
const currentAuthUserId = computed(() => authStore.userId);

// FUNCIONES
const clearBastaCountdown = () => {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value);
    countdownInterval.value = null;
  }
  countdownSeconds.value = 0;
  bastaCallerNickname.value = '';
};

const startBastaCountdown = (bastaCalledAtISO) => {
  clearBastaCountdown();
  const bastaTime = new Date(bastaCalledAtISO).getTime();
  const countdownDuration = 10 * 1000;

  const updateCountdown = () => {
    const now = new Date().getTime();
    const timeLeft = bastaTime + countdownDuration - now;
    if (timeLeft <= 0) {
      countdownSeconds.value = 0;
      clearBastaCountdown();
      if (!gameIsOverForPlayer.value) {
        gameIsOverForPlayer.value = true;
        $q.notify({ message: '¡TIEMPO! Enviando tus respuestas...', color: 'warning', icon: 'timer_off' });
        handlePlayerSaysBasta(true); // Auto-submit
      }
    } else {
      countdownSeconds.value = Math.ceil(timeLeft / 1000);
    }
  };
  updateCountdown();
  countdownInterval.value = setInterval(updateCountdown, 1000);
};

const initializeAnswers = () => {
  const initial = {};
  if (gameStore.currentCategories) {
    gameStore.currentCategories.forEach(category => initial[category.id] = '');
  }
  answers.value = initial;
};

const updateAnswer = (categoryId, value) => {
  answers.value[categoryId] = value;
};

const handlePlayerSaysBasta = async (isTimeUpAutoSubmit = false) => {
  if (gameIsOverForPlayer.value && !isTimeUpAutoSubmit) return;

  isSubmittingBasta.value = true;
  const success = await roomStore.playerSaysBasta(answers.value);
  if (success) {
    gameIsOverForPlayer.value = true;
    if (!isTimeUpAutoSubmit) {
        $q.notify({ type: 'info', message: '¡BASTA! Tus respuestas enviadas. Esperando a los demás.' });
    }
  } else {
    $q.notify({ type: 'negative', message: roomStore.roomError || 'Error al enviar BASTA.' });
  }
  isSubmittingBasta.value = false;
};

const setupGameRoomRealtimeSubscription = () => {
  if (!currentRoomDetails.value?.id) {
    console.warn('GamePage: No currentRoom ID for GameRoomRealtime subscription.');
    return;
  }
  const roomId = currentRoomDetails.value.id;

  if (gameRoomUpdateChannel) {
    supabase.removeChannel(gameRoomUpdateChannel).catch(err => console.error("Error removing old gameRoomUpdateChannel", err));
    gameRoomUpdateChannel = null;
  }

  console.log(`GamePage: Setting up Realtime for game_rooms, room_id: ${roomId}`);
  gameRoomUpdateChannel = supabase
    .channel(`game-${roomId}-state`)
    .on(
      'postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'game_rooms', filter: `id=eq.${roomId}` },
      (payload) => {
        console.log('GamePage: Realtime [game_rooms] UPDATE received!', JSON.parse(JSON.stringify(payload.new)));
        if (payload.new) {
          roomStore._updateCurrentRoomDetails(payload.new);
        }
      }
    )
    .subscribe((status, error) => {
      if (status === 'SUBSCRIBED') {
        console.log(`GamePage: Successfully SUBSCRIBED to [game_rooms] changes for room ${roomId}!`);
      } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
        console.error(`GamePage: Realtime [game_rooms] subscription error. Status: ${status}`, error);
      } else { console.log(`GamePage: Realtime [game_rooms] subscription status: ${status}`, error); }
    });
};

const cleanupGameRoomRealtimeSubscription = () => {
  if (gameRoomUpdateChannel) {
    console.log('GamePage: Cleaning up [game_rooms] Realtime channel.');
    supabase.removeChannel(gameRoomUpdateChannel).catch(err => console.error("Error removing gameRoomUpdateChannel", err));
    gameRoomUpdateChannel = null;
  }
};

onMounted(async () => {
  isLoadingPageData.value = true;
  pageError.value = null;
  gameIsOverForPlayer.value = false;
  isSubmittingBasta.value = false;
  clearBastaCountdown();

  if (!authStore.isAuthenticated || !currentRoomDetails.value?.id) {
    $q.notify({ type: 'negative', message: 'No estás en una sala de juego válida o no has iniciado sesión.' });
    router.replace('/');
    isLoadingPageData.value = false;
    return;
  }

  if (gameStore.themes.length === 0) {
    await gameStore.fetchThemes();
  }
  const themeForRoom = gameStore.themes.find(t => t.id === currentRoomDetails.value.theme_id);
  if (themeForRoom) {
    gameStore.currentThemeForRoom = themeForRoom;
  } else if (currentRoomDetails.value.theme_id) {
    pageError.value = `No se encontró la temática con ID: ${currentRoomDetails.value.theme_id}`;
  }

  if (currentRoomDetails.value.theme_id) {
    await gameStore.fetchCategoriesForTheme(currentRoomDetails.value.theme_id);
    initializeAnswers();
  } else {
    pageError.value = "La sala actual no tiene una temática definida.";
  }
  
  if (!currentRoomDetails.value.current_letter) {
    pageError.value = "No se ha definido una letra para esta ronda.";
  }

  isLoadingPageData.value = false;

  if (currentRoomDetails.value?.id) {
    setupGameRoomRealtimeSubscription();
  }
});

onUnmounted(() => {
  clearBastaCountdown();
  cleanupGameRoomRealtimeSubscription();
});

watch(currentRoomDetails, (newRoomState, oldRoomState) => {
  const myId = currentAuthUserId.value; // Usar la computed para el ID del usuario actual
  const myIdForLog = myId || 'NO_AUTH_ID_YET';

  if (!newRoomState) {
    console.log(`GamePage Watcher (MyID: ${myIdForLog}): currentRoom es null. Limpiando conteo.`);
    clearBastaCountdown();
    if (oldRoomState) { // Solo redirigir si antes había una sala y ahora no
      console.log(`GamePage Watcher (MyID: ${myIdForLog}): Redirigiendo a / porque currentRoom se volvió null.`);
      router.replace('/');
    }
    return;
  }

  console.log(`GamePage Watcher (MyID: ${myIdForLog}): roomStore.currentRoom cambió.`);
  console.log(`  New State Details: status: ${newRoomState.status}, basta_caller_id: ${newRoomState.current_round_basta_caller_id}, basta_called_at: ${newRoomState.current_round_basta_called_at}, my gameIsOverForPlayer: ${gameIsOverForPlayer.value}`);

  // --- Lógica para reaccionar al estado 'scoring' ---
  if (newRoomState.status === 'scoring') {
    console.log(`GamePage Watcher (MyID: ${myIdForLog}): Room status es AHORA 'scoring'. Preparando para resultados.`);
    gameIsOverForPlayer.value = true; // Asegurar que todos los inputs estén bloqueados
    clearBastaCountdown(); // Limpiar cualquier conteo residual
    showingRoundResults.value = false; // O true si vas a mostrar "Calculando..."
                                      // El template ya tiene una sección para esto:
                                      // <div v-if="gameIsOverForPlayer && !showingRoundResults" ...>
                                      //   <div v-if="roomStore.currentRoom?.status === 'scoring'">
                                      //     Calculando puntajes...
                                      //   </div>
                                      // </div>
    // Aquí es donde más adelante llamarías a una acción para obtener los resultados de la ronda.
  } 
  // --- Lógica para reaccionar al estado 'in_progress' (para el BASTA y conteo) ---
  else if (newRoomState.status === 'in_progress') {
    if (newRoomState.current_round_basta_caller_id && newRoomState.current_round_basta_called_at) {
      // Alguien ha cantado BASTA
      const callerId = newRoomState.current_round_basta_caller_id;
      const amICaller = myId === callerId;
      
      console.log(`  BASTA DETECTADO por watcher: CallerID: ${callerId}, MyID: ${myId}, AmICaller: ${amICaller}, GameIsOverForMe(antes de decisión): ${gameIsOverForPlayer.value}`);

      if (!amICaller && !gameIsOverForPlayer.value) {
        // Este es otro jugador, y yo no he dicho BASTA todavía
        console.log("  DECISIÓN DEL WATCHER: Iniciar conteo para mí (no soy el caller y mi juego no ha terminado).");
        const participantWhoCalledBasta = roomStore.participants.find(p => p.user_id === callerId);
        bastaCallerNickname.value = participantWhoCalledBasta ? participantWhoCalledBasta.nickname : 'Alguien';
        startBastaCountdown(newRoomState.current_round_basta_called_at);
      } else if (amICaller) {
        console.log("  DECISIÓN DEL WATCHER: Yo soy el caller. No inicio conteo para mí (mis campos ya deberían estar bloqueados por handlePlayerSaysBasta).");
      } else if (gameIsOverForPlayer.value) {
        // No soy el caller, pero mi juego ya terminó (quizás el conteo terminó para mí)
        console.log("  DECISIÓN DEL WATCHER: No soy el caller, PERO mi juego ya terminó. No inicio conteo.");
      }
    } else {
      // No hay current_round_basta_caller_id, podría ser inicio de ronda normal o reseteo para siguiente ronda.
      console.log("  El estado es 'in_progress' pero no hay información de quién cantó BASTA (o es nueva ronda). Limpiando conteo.");
      clearBastaCountdown();
      // Si es una nueva ronda (ej. newRoomState.current_round_number > oldRoomState?.current_round_number),
      // aquí es donde resetearías gameIsOverForPlayer.value = false; y los 'answers.value'.
      // Esta lógica la implementaremos cuando hagamos "Siguiente Ronda".
    }
  } 
  // --- Lógica para cuando el juego ya no está en progreso (ej. 'finished' o vuelve a 'waiting' inesperadamente) ---
  else if (newRoomState.status !== 'in_progress' && oldRoomState?.status === 'in_progress') {
    // El juego terminó o fue a otro estado que no es 'scoring' ni 'in_progress'
    console.log(`  El estado del juego cambió de 'in_progress' a '${newRoomState.status}'. Limpiando conteo y marcando juego terminado.`);
    clearBastaCountdown();
    gameIsOverForPlayer.value = true; // Asegurar que los campos se bloqueen
  }
}, { deep: true, immediate: true });

watch(() => gameStore.currentCategories, (newCategories) => {
  if (newCategories && newCategories.length > 0) {
    initializeAnswers();
  }
}, { deep: true });
</script>

<style lang="scss" scoped>
.text-h4, .text-h5, .text-h6 {
  color: $primary;
}
</style>