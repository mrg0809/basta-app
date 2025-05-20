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
      
      <div v-if="showingRoundResults && roomStore.currentRoundResults" class="q-mt-lg">
        <q-card>
          <q-card-section class="bg-secondary text-white">
            <div class="text-h6">Resultados de la Ronda {{ roomStore.currentRoundResults.round_number }} - Letra: {{ roomStore.currentRoundResults.current_letter }}</div>
          </q-card-section>
          <q-markup-table flat bordered wrap-cells>
            <thead>
              <tr>
                <th class="text-left">Jugador</th>
                <th v-for="category in roomStore.currentRoundResults.categories" :key="category.id" class="text-left">
                  {{ category.name }}
                </th>
                <th class="text-right">Total Ronda</th>
                <th class="text-right">Total Acumulado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pResult in roomStore.currentRoundResults.results_by_participant" :key="pResult.participant_id">
                <td class="text-left">
                  <q-chip :label="pResult.nickname" dense size="sm" :color="pResult.user_id === authStore.userId ? 'orange' : 'grey-7'" text-color="white" />
                </td>
                <td v-for="category in roomStore.currentRoundResults.categories" :key="category.id" class="text-left">
                  <div v-if="pResult.answers[category.id]">
                    <div>{{ pResult.answers[category.id].text || '-' }}</div>
                    <q-chip dense size="xs" 
                      :color="pResult.answers[category.id].score === 100 ? 'positive' : (pResult.answers[category.id].score === 50 ? 'warning' : (pResult.answers[category.id].score === 0 && pResult.answers[category.id].is_valid === false ? 'negative' : 'grey'))" 
                      text-color="white">
                      {{ pResult.answers[category.id].score }} pts
                      <q-tooltip v-if="pResult.answers[category.id].notes" content-style="font-size: 12px">
                        {{ pResult.answers[category.id].notes }}
                      </q-tooltip>
                    </q-chip>
                  </div>
                  <div v-else>- (0 pts)</div>
                </td>
                <td class="text-right text-weight-bold">{{ pResult.round_score }}</td>
                <td class="text-right text-weight-bold">{{ pResult.total_score }}</td>
              </tr>
            </tbody>
          </q-markup-table>

          <q-card-actions align="right" class="q-mt-md" v-if="roomStore.currentRoom?.status === 'round_over_results'">
            <div v-if="isHostOfThisGame">
              <q-btn 
                v-if="roomStore.currentRoom.current_round_number < MAX_ROUNDS_FOR_GAME"
                label="Iniciar Siguiente Ronda" 
                color="primary"
                @click="handleNextRound"
                :loading="roomStore.isLoadingRoom"
              />
              <q-btn 
                v-else 
                label="Ver Puntajes Finales" 
                color="positive" 
                @click="handleShowFinalScores" />
            </div>
            <div v-else>
              Esperando que el host inicie la siguiente ronda...
            </div>
          </q-card-actions>

          <div v-if="roomStore.currentRoom?.status === 'finished'" class="q-mt-lg text-center">
              <div class="text-h5">¡Juego Terminado!</div>
              <q-btn label="Volver al Inicio" color="primary" to="/" class="q-mt-md"/>
          </div>

        </q-card>
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
const lastProcessedRoundNumber = ref(0)

let gameRoomUpdateChannel = null;

// COMPUTEDS que SÍ se usan o podrían usarse internamente o en el template
const currentRoomDetails = computed(() => roomStore.currentRoom);
const currentAuthUserId = computed(() => {
  // Log para ver cuándo se recalcula esta computed y qué valor tiene user.id
  console.log('Computed currentAuthUserId: authStore.user?.id =', authStore.user?.id);
  return authStore.user?.id || null;
});

const isHostOfThisGame = computed(() => {
  const authId = currentAuthUserId.value; // ID del usuario logueado
  const hostIdInRoom = currentRoomDetails.value?.host_user_id; // ID del host de la sala actual

  // Logs para depuración:
  console.log('Computed isHostOfThisGame: Verificando...');
  console.log(`  - Auth User ID (currentAuthUserId.value): ${authId}`);
  console.log(`  - Room's Host ID (currentRoomDetails.value?.host_user_id): ${hostIdInRoom}`);
  
  if (!currentRoomDetails.value || !authId) {
    console.log('  - Pre-condiciones NO cumplidas (no hay sala actual o no hay ID de usuario autenticado). Devuelve: false');
    return false;
  }
  
  const decision = hostIdInRoom === authId;
  console.log(`  - Comparación: '${hostIdInRoom}' === '${authId}'  Resultado: ${decision}`);
  return decision;
});

const MAX_ROUNDS_FOR_GAME = 3;

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

const handleNextRound = async () => {
  await roomStore.goToNextRound();
};

const handleShowFinalScores = () => {
  // Si los resultados ya se muestran, esto podría no hacer nada nuevo,
  // o podrías navegar a una página de "Game Over" más elaborada.
  $q.notify('Mostrando puntajes finales (ya visibles o lógica pendiente).');
  // Podrías querer asegurar que showingRoundResults.value = true aquí.
  if (roomStore.currentRoundResults) {
      showingRoundResults.value = true;
  }
};

const resetForNewRound = () => {
  console.log("GamePage: Reseteando para nueva ronda.");
  initializeAnswers(); // Limpia las respuestas
  gameIsOverForPlayer.value = false;
  isSubmittingBasta.value = false;
  showingRoundResults.value = false; // Ocultar tabla de resultados
  clearBastaCountdown(); // Limpiar cualquier conteo
  pageError.value = null; // Limpiar errores de página
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

watch(currentRoomDetails, async (newRoomState, oldRoomState) => {
  const myId = currentAuthUserId.value;
  const myIdForLog = myId || 'NO_AUTH_ID_YET';

  if (!newRoomState) {
    console.log(`GamePage Watcher (MyID: ${myIdForLog}): currentRoom es null. Limpiando todo y reseteando ronda procesada.`);
    resetForNewRound();
    lastProcessedRoundNumber.value = 0; // Resetear al salir de la sala
    if (oldRoomState) {
      console.log(`GamePage Watcher (MyID: ${myIdForLog}): Redirigiendo a / porque currentRoom se volvió null.`);
      router.replace('/');
    }
    return;
  }

  console.log(`GamePage Watcher (MyID: ${myIdForLog}): roomStore.currentRoom cambió.`);
  console.log(`  New State: status=${newRoomState.status}, round=${newRoomState.current_round_number}, letter=${newRoomState.current_letter}, basta_caller=${newRoomState.current_round_basta_caller_id}, my gameIsOverForPlayer=${gameIsOverForPlayer.value}, lastProcessedRound=${lastProcessedRoundNumber.value}`);
  if (oldRoomState) {
    console.log(`  Old State: status=${oldRoomState.status}, round=${oldRoomState.current_round_number}`);
  }

  // --- MANEJO DE ESTADOS DE LA SALA ---
  if (newRoomState.status === 'finished') {
    console.log(`GamePage Watcher (MyID: ${myIdForLog}): Room status es 'finished'. Juego terminado.`);
    gameIsOverForPlayer.value = true;
    clearBastaCountdown();
    lastProcessedRoundNumber.value = newRoomState.current_round_number; // Marcar como procesada
  } 
  else if (newRoomState.status === 'round_over_results') {
    console.log(`GamePage Watcher (MyID: ${myIdForLog}): Room status es 'round_over_results'. Fetching results.`);
    gameIsOverForPlayer.value = true; // Los inputs deben estar bloqueados
    clearBastaCountdown();
    showingRoundResults.value = false; 
    
    await roomStore.fetchRoundResults();

    if (roomStore.currentRoundResults) {
      showingRoundResults.value = true;
      console.log(`GamePage Watcher (MyID: ${myIdForLog}): Resultados de ronda cargados.`);
    } else {
      pageError.value = roomStore.roomError || "No se pudieron cargar los resultados de la ronda.";
      console.error(`GamePage Watcher (MyID: ${myIdForLog}): Error al cargar resultados - ${pageError.value}`);
    }
    lastProcessedRoundNumber.value = newRoomState.current_round_number; // Marcar esta ronda como vista en sus resultados
  } 
  else if (newRoomState.status === 'scoring') {
    console.log(`GamePage Watcher (MyID: ${myIdForLog}): Room status es 'scoring'.`);
    gameIsOverForPlayer.value = true; // Los inputs siguen bloqueados
    clearBastaCountdown();
    showingRoundResults.value = false;
    // No actualizamos lastProcessedRoundNumber aquí, esperamos a 'round_over_results'
  } 
  else if (newRoomState.status === 'in_progress') {
    console.log(`GamePage Watcher (MyID: ${myIdForLog}): Room status es 'in_progress'.`);
    
    // --- DETECCIÓN DE NUEVA RONDA USANDO lastProcessedRoundNumber ---
    const isNewRoundDetected = newRoomState.current_round_number > lastProcessedRoundNumber.value &&
                               !newRoomState.current_round_basta_caller_id;

    if (isNewRoundDetected) {
      console.log(`GamePage Watcher (MyID: ${myIdForLog}): DETECTADA NUEVA RONDA ${newRoomState.current_round_number} (UI estaba en ${lastProcessedRoundNumber.value}). Reseteando UI.`);
      resetForNewRound();
      lastProcessedRoundNumber.value = newRoomState.current_round_number; // Actualizar la última ronda que la UI está configurando/jugando
    }
    // -----------------------------------------------------------------

    // Lógica para el conteo de BASTA (si alguien ya cantó en ESTA ronda 'in_progress')
    // Esta se ejecuta después del posible reseteo si es una nueva ronda.
    // Si fue una nueva ronda, gameIsOverForPlayer.value será false aquí.
    if (newRoomState.current_round_basta_caller_id && newRoomState.current_round_basta_called_at) {
      const callerId = newRoomState.current_round_basta_caller_id;
      const amICaller = myId === callerId;
      
      console.log(`  BASTA DETECTADO por watcher: CallerID: ${callerId}, MyID: ${myId}, AmICaller: ${amICaller}, GameIsOverForMe(antes de decisión): ${gameIsOverForPlayer.value}`);

      if (!amICaller && !gameIsOverForPlayer.value) {
        console.log("  DECISIÓN DEL WATCHER (BASTA): Iniciar conteo para mí (no soy el caller y mi juego no ha terminado).");
        const participantWhoCalledBasta = roomStore.participants.find(p => p.user_id === callerId);
        bastaCallerNickname.value = participantWhoCalledBasta ? participantWhoCalledBasta.nickname : 'Alguien';
        startBastaCountdown(newRoomState.current_round_basta_called_at);
      } else if (amICaller) {
        console.log("  DECISIÓN DEL WATCHER (BASTA): Yo soy el caller.");
      } else if (gameIsOverForPlayer.value) {
        console.log("  DECISIÓN DEL WATCHER (BASTA): No soy caller, PERO mi juego ya terminó para esta ronda.");
      }
    } else if (!isNewRoundDetected) { 
      // Si es 'in_progress', no hay BASTA caller, Y NO es el inicio de una nueva ronda (isNewRoundDetected fue false).
      // Este es el estado normal de juego al inicio de una ronda antes de que alguien diga BASTA.
      // Aseguramos que no haya conteo activo si no corresponde.
      // console.log("  Estado es 'in_progress', no hay BASTA caller (y no es una nueva ronda explícita que acabamos de resetear). Limpiando conteo si estaba activo.");
      if(gameIsOverForPlayer.value === false) { // Solo limpia el conteo si se supone que el jugador está activo
         clearBastaCountdown();
      }
    }
  } 
  else { // Otros estados
    console.log(`  El estado del juego cambió a un estado inesperado o no manejado aquí: '${newRoomState.status}'. Limpiando conteo, marcando juego terminado para UI.`);
    clearBastaCountdown();
    gameIsOverForPlayer.value = true;
    showingRoundResults.value = false;
  }
}, { deep: true, immediate: true });

</script>

<style lang="scss" scoped>
.text-h4, .text-h5, .text-h6 {
  color: $primary;
}
</style>