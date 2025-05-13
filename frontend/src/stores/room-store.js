// src/stores/room-store.js
import { defineStore } from 'pinia';
import { api } from 'boot/axios'; // Nuestra instancia configurada de Axios
import { useAuthStore } from './auth-store'; // Para acceder al ID del usuario si es necesario
import { Notify } from 'quasar'; // Para notificaciones (asumiendo que ya resolvimos cómo usarla aquí o la reemplazamos)

export const useRoomStore = defineStore('room', {
  state: () => ({
    currentRoom: null,      // Objeto: Detalles de la sala actual (de GameRoomResponse)
    isLoadingRoom: false,   // Booleano: Para operaciones de carga de sala
    roomError: null,        // String: Mensajes de error de operaciones de sala
  }),

  getters: {
    hasActiveRoom: (state) => !!state.currentRoom,
    roomId: (state) => state.currentRoom?.id || null,
    roomCode: (state) => state.currentRoom?.room_code || null,
    participants: (state) => state.currentRoom?.room_participants || [], // Usamos room_participants como en el modelo Pydantic corregido
    isCurrentUserHost: (state) => {
        const authStore = useAuthStore();
        console.log('RoomStore Getter: Checking isCurrentUserHost...');
        console.log('  - state.currentRoom present?:', !!state.currentRoom);
        if (state.currentRoom) {
          console.log('  - state.currentRoom.host_user_id:', state.currentRoom.host_user_id);
        }
        console.log('  - authStore.isAuthenticated:', authStore.isAuthenticated);
        console.log('  - authStore.userId:', authStore.userId);
  
        if (!state.currentRoom || !authStore.isAuthenticated || !authStore.userId) {
          console.log('  - Pre-conditions failed. Returning false.');
          return false;
        }
        const decision = state.currentRoom.host_user_id === authStore.userId;
        console.log(`  - Comparison: ${state.currentRoom.host_user_id} === ${authStore.userId}  Result: ${decision}`);
        return decision;
      },
  },

  actions: {
    // Acción interna para establecer la sala actual
    _setRoom(roomData) {
      this.currentRoom = roomData;
      this.roomError = null;
      // console.log('RoomStore: Current room set', this.currentRoom);
    },

    // Acción para limpiar la sala actual
    clearRoom() {
      this.currentRoom = null;
      this.roomError = null;
      // console.log('RoomStore: Current room cleared');
    },

    // Crear una nueva sala de juego
    async createRoom({ themeId, maxPlayers }) {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        this.roomError = "Debes iniciar sesión para crear una sala.";
        Notify.create({ type: 'negative', message: this.roomError });
        return false;
      }

      this.isLoadingRoom = true;
      this.roomError = null;
      try {
        const payload = { theme_id: themeId };
        if (maxPlayers) {
          payload.max_players = maxPlayers;
        }
        // El token JWT se debería añadir automáticamente por un interceptor de Axios
        // si lo configuramos, o Axios debe estar configurado para enviarlo.
        // Por ahora, el backend espera el token para identificar al usuario.
        const response = await api.post('/rooms/', payload);
        this._setRoom(response.data);
        Notify.create({ type: 'positive', message: `Sala '${response.data.room_code}' creada!` });
        return response.data; // Devuelve los datos de la sala creada
      } catch (error) {
        console.error("Error creating room:", error.response?.data || error.message);
        this.roomError = error.response?.data?.detail || 'Error desconocido al crear la sala.';
        Notify.create({ type: 'negative', message: this.roomError });
        this.clearRoom(); // Limpiar cualquier dato parcial
        return false;
      } finally {
        this.isLoadingRoom = false;
      }
    },

    // Unirse a una sala de juego existente
    async joinRoom({ roomCode, nickname }) {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        this.roomError = "Debes iniciar sesión para unirte a una sala.";
        Notify.create({ type: 'negative', message: this.roomError });
        return false;
      }

      this.isLoadingRoom = true;
      this.roomError = null;
      try {
        const payload = {};
        if (nickname) {
          payload.nickname = nickname;
        }
        const response = await api.post(`/rooms/${roomCode.toUpperCase()}/join/`, payload);
        this._setRoom(response.data);
        Notify.create({ type: 'positive', message: `Te has unido a la sala '${response.data.room_code}'` });
        return response.data; // Devuelve los datos de la sala a la que se unió
      } catch (error) {
        console.error("Error joining room:", error.response?.data || error.message);
        this.roomError = error.response?.data?.detail || 'Error desconocido al unirse a la sala.';
        Notify.create({ type: 'negative', message: this.roomError });
        // No necesariamente limpiamos la sala aquí, porque el usuario podría no estar en una.
        return false;
      } finally {
        this.isLoadingRoom = false;
      }
    },

    // Obtener detalles de una sala (necesitaremos el endpoint GET en el backend)
    async fetchRoomDetails(roomIdOrCode) {
      this.isLoadingRoom = true;
      this.roomError = null;
      try {
        const response = await api.get(`/rooms/${roomIdOrCode}/`); // Asumiendo que este endpoint existirá
        this._setRoom(response.data);
        return response.data;
      } catch (error) {
        console.error("Error fetching room details:", error.response?.data || error.message);
        this.roomError = error.response?.data?.detail || 'Error al cargar detalles de la sala.';
        Notify.create({ type: 'negative', message: this.roomError });
        // Considera si quieres this.clearRoom(); aquí
        return null;
      } finally {
        this.isLoadingRoom = false;
      }
    },

    // (Futuro) Salir de una sala
    async leaveRoom() {
      if (!this.currentRoom) return;
      this.isLoadingRoom = true;
      try {
        // await api.post(`/rooms/${this.currentRoom.id}/leave/`); // Asumiendo endpoint
        Notify.create({ type: 'info', message: `Has salido de la sala '${this.currentRoom.room_code}'` });
        this.clearRoom();
      } catch (error) {
        console.error("Error leaving room:", error.response?.data || error.message);
        Notify.create({ type: 'negative', message: 'Error al salir de la sala.' });
      } finally {
        this.isLoadingRoom = false;
      }
    },

    _addParticipant(newParticipant) {
        if (this.currentRoom && newParticipant) {
          // Evitar duplicados si la carga inicial ya lo incluyó o si llega un eco
          const exists = this.currentRoom.room_participants.some(p => p.id === newParticipant.id);
          if (!exists) {
            this.currentRoom.room_participants.push(newParticipant);
            console.log('RoomStore: Participant added via realtime', newParticipant);
          }
        }
      },
    
      _updateParticipant(updatedParticipant) {
        if (this.currentRoom && updatedParticipant) {
          const index = this.currentRoom.room_participants.findIndex(p => p.id === updatedParticipant.id);
          if (index !== -1) {
            // Reemplazar el objeto completo o fusionar campos específicos
            this.currentRoom.room_participants[index] = { ...this.currentRoom.room_participants[index], ...updatedParticipant };
            console.log('RoomStore: Participant updated via realtime', updatedParticipant);
          } else {
            // Si no se encuentra, podría ser un nuevo participante que llegó como UPDATE (raro)
            // O podrías querer añadirlo si la lógica lo permite
            this.currentRoom.room_participants.push(updatedParticipant);
             console.log('RoomStore: Participant (that was not found for update) added via realtime update event', updatedParticipant);
          }
        }
      },
    
      _removeParticipant(participantId) {
        if (this.currentRoom && participantId) {
          this.currentRoom.room_participants = this.currentRoom.room_participants.filter(p => p.id !== participantId);
          console.log('RoomStore: Participant removed via realtime', participantId);
        }
      },

      async setMyReadyStatus(isReady) {
        if (!this.currentRoom || !this.currentRoom.id) {
          console.error("RoomStore: No current room to set ready status for.");
          Notify.create({ type: 'negative', message: "No estás en una sala activa." });
          return false;
        }
        // No necesitamos el participantId aquí ya que el backend usa el token del usuario
        // const authStore = useAuthStore();
        // const myParticipant = this.participants.find(p => p.user_id === authStore.userId);
        // if (!myParticipant) {
        //   console.error("RoomStore: Current user not found in participants list.");
        //   return false;
        // }
    
        this.isLoadingRoom = true; // Podrías tener un flag de loading más específico
        try {
          // El backend usa el token para identificar al usuario,
          // así que solo necesitamos enviar el nuevo estado 'is_ready'.
          await api.patch(`/rooms/${this.currentRoom.id}/participants/me/ready`, {
            is_ready: isReady,
          });
    
          // El evento de Realtime debería actualizar el estado del participante en el store.
          // Por lo tanto, no necesitamos actualizarlo manualmente aquí a partir de `response.data`.
          // Si Realtime fallara o quisieras una actualización optimista, podrías hacerlo:
          // this._updateParticipant(response.data); 
          
          Notify.create({
            type: 'info',
            message: `Tu estado ahora es: ${isReady ? '¡Listo!' : 'No listo.'}`,
            // No es necesario, ya que Realtime lo actualizará visualmente.
            // Si la notificación viene del evento de Realtime, es aún mejor.
          });
          return true;
        } catch (error) {
          console.error("Error setting ready status:", error.response?.data || error.message);
          Notify.create({
            type: 'negative',
            message: error.response?.data?.detail || 'Error al cambiar tu estado de listo.',
          });
          return false;
        } finally {
          this.isLoadingRoom = false;
        }
      },

      async startGame() {
        const authStore = useAuthStore();
  
        // --- VERIFICACIÓN DIRECTA CON console.log ---
        const currentRoomExists = !!this.currentRoom;
        const currentRoomHostId = this.currentRoom?.host_user_id;
        const currentAuthUserId = authStore.user?.id;
        const userIsAuthenticated = authStore.isAuthenticated;
        const isHostByDirectCheck = currentRoomExists && userIsAuthenticated && currentAuthUserId && (currentRoomHostId === currentAuthUserId);
  
        console.log(`RoomStore Action startGame:
          - currentRoom exists? ${currentRoomExists}
          - currentRoom.host_user_id: ${currentRoomHostId}
          - authStore.isAuthenticated: ${userIsAuthenticated}
          - authStore.user.id (direct access): ${currentAuthUserId}
          - Comparison for host: ${currentRoomHostId} === ${currentAuthUserId} -> ${isHostByDirectCheck}`);
  
        if (!isHostByDirectCheck) { // Usamos la verificación directa
          this.roomError = "Solo el host puede iniciar el juego, o no estás en una sala válida, o no se pudo verificar tu identidad como host.";
          console.error("RoomStore: startGame guard failed. Details:", { currentRoomExists, currentRoomHostId, userIsAuthenticated, currentAuthUserId });
          // Notify.create({ type: 'negative', message: this.roomError }); // Comentado
          this.isLoadingRoom = false;
          return false;
        }
        // --- FIN VERIFICACIÓN ---
  
        // La lógica de canStartGame (todos listos, etc.) la validará el backend.
        // Aquí solo verificamos que el que llama sea el host de la sala actual.
  
        this.isLoadingRoom = true;
        this.roomError = null;
        try {
          console.log(`RoomStore: Attempting to start game for room ID: ${this.currentRoom.id}`);
          const response = await api.post(`/rooms/${this.currentRoom.id}/start`);
          
          console.log('RoomStore: Start game request successful. Backend response data:', response.data);
          // La navegación y actualización del estado de la sala (status, letra)
          // se manejarán a través de la suscripción de Realtime a 'game_rooms' en RoomLobbyPage.vue
          return true; 
        } catch (error) {
          console.error("Error starting game in store action:", error.response?.data || error.message);
          this.roomError = error.response?.data?.detail || 'Error desconocido al iniciar el juego.';
          // Notify.create({ type: 'negative', message: this.roomError }); // Comentado
          return false;
        } finally {
          this.isLoadingRoom = false;
        }
      },

    // (Futuro) Marcarse como listo
    async setReadyStatus(isReady) {
        if (!this.currentRoom || !useAuthStore().userId) return;
        const participantId = this.participants.find(p => p.user_id === useAuthStore().userId)?.id;
        if (!participantId) return;

        this.isLoadingRoom = true; // Podría ser un loading específico para esta acción
        try {
            // await api.post(`/rooms/<span class="math-inline">\{this\.currentRoom\.id\}/participants/</span>{participantId}/ready`, { is_ready: isReady });
            // La actualización del estado local de los participantes vendría idealmente de Supabase Realtime
            // o recargando los detalles de la sala.
            // Por ahora, actualizamos localmente para simular:
            const participant = this.participants.find(p => p.id === participantId);
            if (participant) participant.is_ready = isReady;

            Notify.create({ type: 'info', message: `Tu estado ahora es: ${isReady ? 'Listo' : 'No Listo'}`});
        } catch (error) {
            console.error("Error setting ready status:", error);
            Notify.create({ type: 'negative', message: 'Error al cambiar estado de listo.' });
        } finally {
            this.isLoadingRoom = false;
        }
    }
    
  },
});