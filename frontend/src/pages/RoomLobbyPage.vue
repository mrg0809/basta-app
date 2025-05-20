<template>
    <q-page padding>
      <div v-if="roomStore.isLoadingRoom && !roomStore.currentRoom" class="fixed-center text-center">
        <q-spinner color="primary" size="3em" />
        <div class="q-mt-md">Cargando detalles de la sala...</div>
      </div>
  
      <div v-else-if="roomStore.roomError && !roomStore.currentRoom" class="text-negative text-center q-mt-xl">
        <q-icon name="error_outline" size="2em" />
        <div>Error al cargar la sala: {{ roomStore.roomError }}</div>
        <q-btn label="Volver" color="primary" class="q-mt-md" @click="goBack" />
      </div>
  
      <div v-else-if="roomStore.currentRoom" class="row justify-center">
        <div class="col-12 col-md-10 col-lg-8">
          <q-card>
            <q-card-section class="bg-primary text-white">
              <div class="text-h6">Lobby de la Sala: {{ roomStore.currentRoom.room_code }}</div>
              <div class="text-subtitle2">Temática: {{ themeName }}</div>
            </q-card-section>
  
            <q-separator />
  
            <q-card-section>
              <div class="row items-center q-mb-md">
                <div class="text-subtitle1">Código de Sala:</div>
                <q-chip outline color="secondary" text-color="white" class="q-ml-sm cursor-pointer" @click.capture="copyRoomCode">
                  {{ roomStore.currentRoom.room_code }}
                  <q-tooltip>Copiar código</q-tooltip>
                </q-chip>
                <q-space />
                <q-btn
                  label="Salir de la Sala"
                  color="negative"
                  icon="logout"
                  @click="handleLeaveRoom"
                  :loading="roomStore.isLoadingRoom"
                  outline
                />
              </div>
  
              <div class="text-h6 q-mb-sm">Participantes ({{ roomStore.participants.length }} / {{ roomStore.currentRoom.max_players }})</div>
              <q-list bordered separator v-if="roomStore.participants.length > 0">
                <q-item v-for="participant in roomStore.participants" :key="participant.id">
                    <q-item-section avatar>
                        <q-icon 
                        :name="participant.is_ready === true ? 'check_circle' : (participant.is_ready === false ? 'hourglass_empty' : 'help_outline')" 
                        :color="participant.is_ready === true ? 'positive' : (participant.is_ready === false ? 'grey' : 'warning')" 
                        size="sm" 
                        class="q-mr-sm"
                        />
                        <div style="font-size: 0.6em; line-height: 1; white-space: nowrap;">
                        R:{{ String(participant.is_ready) }}({{ typeof participant.is_ready }})
                        </div>
                    </q-item-section>
                    
                    <q-item-section>
                        <q-item-label>{{ participant.nickname }}</q-item-label>
                        <q-item-label caption style="font-size: 0.7em; word-break: break-all;">
                        P-ID: {{ participant.user_id }}
                        </q-item-label>
                        <q-item-label caption v-if="participant.user_id === roomStore.currentRoom.host_user_id">
                        (Host)
                        </q-item-label>
                        <q-item-label caption v-if="participant.user_id === currentAuthUserId && participant.user_id !== roomStore.currentRoom.host_user_id">
                        (Tú) </q-item-label>
                        <q-item-label caption v-if="participant.user_id === currentAuthUserId && participant.user_id === roomStore.currentRoom.host_user_id">
                        (Tú - Host) </q-item-label>
                    </q-item-section>

                    <q-item-section side v-if="participant.user_id === currentAuthUserId">
                        <q-btn
                            dense
                            flat
                            :icon="participant.is_ready ? 'radio_button_checked' : 'radio_button_unchecked'"
                            :label="participant.is_ready ? 'No Listo' : '¡Estoy Listo!'"
                            @click="toggleMyReadyStatus(participant.is_ready)"
                            :color="participant.is_ready ? 'green-7' : 'orange-7'"
                            :loading="roomStore.isLoadingRoom" 
                        />
                    </q-item-section>
                    </q-item> 
                </q-list>
              <div v-else class="text-grey-7 q-py-md">
                Esperando jugadores... ¡Comparte el código de la sala!
              </div>
            </q-card-section>
  
            <q-card-actions align="right" v-if="amITheHost">
              <q-btn
                label="Iniciar Juego"
                color="positive"
                icon="play_arrow"
                @click="handleStartGame"
                :disable="!canStartGame"
                :loading="roomStore.isLoadingRoom"
              />
            </q-card-actions>
          </q-card>
        </div>
      </div>
      <div v-else-if="!roomStore.isLoadingRoom" class="text-center q-mt-xl">
          <div class="text-h6">Sala no encontrada o no se pudo cargar.</div>
          <q-btn label="Ir a Inicio" color="primary" class="q-mt-md" to="/" />
      </div>
    </q-page>
  </template>
  
  <script setup>
  import { onMounted, onUnmounted, computed, watch } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useRoomStore } from 'stores/room-store';
  import { useGameStore } from 'stores/game-store';
  import { useAuthStore } from 'stores/auth-store';
  import { useQuasar, copyToClipboard } from 'quasar'; 
  import { supabase } from 'boot/supabase-client';
  
  const route = useRoute();
  const router = useRouter();
  const roomStore = useRoomStore();
  const gameStore = useGameStore();
  const authStore = useAuthStore();
  const $q = useQuasar();

  const currentAuthUserId = computed(() => authStore.user?.id || null);

  const amITheHost = computed(() => {
  // Replicamos la lógica del getter para asegurar la reactividad local al authStore.userId
  if (!roomStore.currentRoom || !authStore.user?.id) { // Usamos authStore.user?.id directamente
    return false;
  }
  // Log para esta computada específica
  // console.log(`RoomLobbyPage computed amITheHost: room.host_id=${roomStore.currentRoom.host_user_id}, auth.user_id=${authStore.user?.id}`);
  return roomStore.currentRoom.host_user_id === authStore.user.id;
});
  
  let participantsChannel = null;
  let gameRoomChannel = null;
  
  const roomIdFromRoute = computed(() => route.params.roomId);
  
  const themeName = computed(() => {
    if (roomStore.currentRoom && gameStore.themes.length > 0) {
      const theme = gameStore.themes.find(t => t.id === roomStore.currentRoom.theme_id);
      return theme ? theme.name : 'Desconocida';
    }
    return 'Cargando temática...';
  });
  
  const canStartGame = computed(() => {
    // if (!roomStore.isCurrentUserHost || ...) // Antes
    if (!amITheHost.value || !roomStore.currentRoom || roomStore.participants.length < 1) { // Ahora usa amITheHost.value
        return false;
    }
    const allReady = roomStore.participants.every(p => p.is_ready);
    // console.log('RoomLobbyPage Computed: canStartGame - amITheHost:', amITheHost.value, 'participants.length:', roomStore.participants.length, 'allReady:', allReady);
    return allReady;
    });
    
  
  const loadRoomDetails = async () => {
    const roomId = roomIdFromRoute.value;
    if (roomId) {
      if (!roomStore.currentRoom || roomStore.currentRoom.id !== roomId) {
        await roomStore.fetchRoomDetails(roomId);
      }
    } else {
      console.error("RoomLobbyPage: No roomId found in route params.");
      router.replace('/');
    }
  };
  
  const setupRealtimeSubscriptions = () => {
    if (!roomStore.currentRoom?.id) {
        console.warn('setupRealtimeSubscriptions: No currentRoom ID available, cannot subscribe.');
        return;
    }

    const roomId = roomStore.currentRoom.id;
    console.log(`RoomLobbyPage: Setting up Realtime subscriptions for room_id: ${roomId}`);

    // --- 1. Suscripción a CAMBIOS EN PARTICIPANTES (room_participants) ---
    if (participantsChannel) {
        console.log('RoomLobbyPage: Removing previous participants channel before re-subscribing.');
        supabase.removeChannel(participantsChannel).catch(err => console.error("Error removing old participants channel", err));
        participantsChannel = null;
    }
    
    participantsChannel = supabase
        .channel(`room-${roomId}-participants`) // Nombre de canal único para participantes de esta sala
        .on(
        'postgres_changes',
        {
            event: '*', // Escuchar INSERT, UPDATE, DELETE
            schema: 'public',
            table: 'room_participants',
            filter: `game_room_id=eq.${roomId}` // Solo cambios para esta sala
        },
        (payload) => {
            console.log('RoomLobbyPage: Realtime [room_participants] change received!', payload);
            if (payload.eventType === 'INSERT') {
            roomStore._addParticipant(payload.new);
            } else if (payload.eventType === 'UPDATE') {
            roomStore._updateParticipant(payload.new);
            } else if (payload.eventType === 'DELETE') {
            if (payload.old && typeof payload.old.id !== 'undefined') {
                roomStore._removeParticipant(payload.old.id);
            } else {
                console.warn('Realtime DELETE event for participant missing old.id, re-fetching details for safety.');
                roomStore.fetchRoomDetails(roomId); // Fallback
            }
            }
        }
        )
        .subscribe((status, error) => {
        if (status === 'SUBSCRIBED') {
            console.log(`RoomLobbyPage: Successfully SUBSCRIBED to [room_participants] changes for room ${roomId}!`);
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
            console.error(`RoomLobbyPage: Realtime [room_participants] subscription error or timeout. Status: ${status}`, error);
        } else if (status === 'CLOSED') {
            console.log(`RoomLobbyPage: Realtime [room_participants] subscription CLOSED for room ${roomId}.`);
        } else {
            console.log(`RoomLobbyPage: Realtime [room_participants] subscription status: ${status}`, error);
        }
        });

    // --- 2. Suscripción a CAMBIOS EN LA SALA (game_rooms) ---
    // (Para detectar inicio de juego, cambio de letra, etc.)
    if (gameRoomChannel) {
        console.log('RoomLobbyPage: Removing previous game_room channel before re-subscribing.');
        supabase.removeChannel(gameRoomChannel).catch(err => console.error("Error removing old game_room channel", err));
        gameRoomChannel = null;
    }

    gameRoomChannel = supabase
        .channel(`room-${roomId}-details`) // Nombre de canal único para detalles de esta sala
        .on(
        'postgres_changes',
        {
            event: 'UPDATE', // Principalmente nos interesan los updates para esta sala (status, current_letter)
            schema: 'public',
            table: 'game_rooms',
            filter: `id=eq.${roomId}` // Filtra por el ID de esta sala
        },
        (payload) => {
            console.log('RoomLobbyPage: Realtime [game_rooms] change received!', payload);
            if (payload.new) {
            // Actualiza los detalles de la sala en el store.
            // Es importante fusionar para no perder la lista de room_participants que se maneja por separado.
            const currentParticipants = roomStore.currentRoom?.room_participants || [];
            roomStore._setRoom({ ...payload.new, room_participants: currentParticipants });

            // Si el juego ha comenzado (estado y letra están presentes)
            if (payload.new.status === 'in_progress' && payload.new.current_letter) {
                $q.notify({ // Asegúrate de que Notify esté disponible o usa $q.notify
                message: `¡El juego ha comenzado! Letra: ${payload.new.current_letter}`,
                color: 'positive',
                icon: 'play_circle_filled'
                });
                
                // Navegar a la página del juego.
                // GamePage necesitará acceder a roomStore.currentRoom para la letra, temática, etc.
                router.push({ 
                name: 'GamePage', 
                // Opcional: pasar roomId como parámetro si GamePage no lo obtiene siempre del store
                // params: { roomId: roomId } 
                });
            }
            }
        }
        )
        .subscribe((status, error) => {
        if (status === 'SUBSCRIBED') {
            console.log(`RoomLobbyPage: Successfully SUBSCRIBED to [game_rooms] changes for room ${roomId}!`);
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
            console.error(`RoomLobbyPage: Realtime [game_rooms] subscription error or timeout. Status: ${status}`, error);
        } else if (status === 'CLOSED') {
            console.log(`RoomLobbyPage: Realtime [game_rooms] subscription CLOSED for room ${roomId}.`);
        } else {
            console.log(`RoomLobbyPage: Realtime [game_rooms] subscription status: ${status}`, error);
        }
        });
    };
  
  const cleanupRealtimeSubscriptions = () => {
    if (participantsChannel) {
        supabase.removeChannel(participantsChannel).catch(console.error);
        participantsChannel = null;
    }
    if (gameRoomChannel) { // <--- Limpiar el nuevo canal
        supabase.removeChannel(gameRoomChannel).catch(console.error);
        gameRoomChannel = null;
    }
    console.log('RoomLobbyPage: Cleaned up realtime subscriptions.');
  };
  

  const toggleMyReadyStatus = async (currentIsReady) => {
    await roomStore.setMyReadyStatus(!currentIsReady);
    // No necesitas hacer nada más aquí, Realtime debería actualizar la UI
    // a través de la acción _updateParticipant en el store.
    };
  
  onMounted(async () => {
    console.log('RoomLobbyPage onMounted: authStore.userId =', authStore.userId);
    roomStore.roomError = null;
    if (gameStore.themes.length === 0) {
      await gameStore.fetchThemes();
    }
    await loadRoomDetails();
    if (roomStore.currentRoom?.id) {
      setupRealtimeSubscriptions();
    }
  });
  
  onUnmounted(() => {
    cleanupRealtimeSubscriptions();
  });
  
  watch(roomIdFromRoute, async (newRoomId, oldRoomId) => {
    if (newRoomId && newRoomId !== oldRoomId) {
      cleanupRealtimeSubscriptions();
      await loadRoomDetails();
      if (roomStore.currentRoom?.id) {
        setupRealtimeSubscriptions();
      }
    }
  });
  
  watch(() => roomStore.currentRoom, (newRoom, oldRoom) => {
      if (newRoom && oldRoom?.id !== newRoom.id) {
          cleanupRealtimeSubscriptions();
          setupRealtimeSubscriptions();
      } else if (!newRoom && oldRoom) {
          cleanupRealtimeSubscriptions();
      }
  }, { deep: true }); // deep: true por si currentRoom es un objeto complejo y sus propiedades internas cambian
  
  const copyRoomCode = () => {
    const codeToCopy = roomStore.currentRoom?.room_code; // Obtener el código

    // --- Log para depuración ---
    console.log('Intentando copiar el código de sala:', codeToCopy);
    console.log('Tipo de dato de codeToCopy:', typeof codeToCopy);
    // ---------------------------

    if (codeToCopy && typeof codeToCopy === 'string' && codeToCopy.trim() !== '') { // Asegurarse de que sea un string no vacío
      copyToClipboard(codeToCopy)
        .then(() => {
          $q.notify({
            message: '¡Código de sala copiado!',
            color: 'positive',
            icon: 'content_copy',
            position: 'top',
            timeout: 1500 // Un timeout corto para la notificación
          });
        })
        .catch((err) => { // <--- Captura el error específico
          console.error('Error al usar copyToClipboard:', err); // <--- Loguea el error
          $q.notify({
            message: 'Error al copiar el código. Revisa la consola.',
            color: 'negative',
            icon: 'error_outline'
          });
        });
    } else {
      console.warn('No se pudo copiar: room_code no es válido o está vacío.', codeToCopy);
      $q.notify({
        message: 'No hay un código de sala válido para copiar.',
        color: 'warning',
        icon: 'warning_amber'
      });
    }
  };
  
  const handleLeaveRoom = async () => {
    $q.dialog({
      title: 'Salir de la Sala',
      message: '¿Estás seguro de que quieres salir de esta sala?',
      cancel: true,
      persistent: true
    }).onOk(async () => {
      cleanupRealtimeSubscriptions();
      await roomStore.leaveRoom();
      router.push('/');
    });
  };
  
  const handleStartGame = async () => {
    if (canStartGame.value) {
        await roomStore.startGame();
        // La navegación ocurrirá cuando el evento de Realtime actualice el estado de la sala
    } else {
        $q.notify({ message: 'No se cumplen las condiciones para iniciar el juego.', color: 'warning' });
    }
  };
  
  const goBack = () => {
    router.go(-1);
  };
  </script>
  
  <style scoped>
  .cursor-pointer { cursor: pointer; }
  </style>