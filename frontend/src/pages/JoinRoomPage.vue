<template>
    <q-page padding>
      <div class="row justify-center">
        <div class="col-12 col-md-8 col-lg-6">
          <q-card class="q-mt-md">
            <q-card-section class="bg-secondary text-white"> <div class="text-h6">Unirse a una Sala Existente</div>
            </q-card-section>
  
            <q-separator />
  
            <q-card-section>
              <q-form @submit.prevent="handleJoinRoom" class="q-gutter-md">
                <q-input
                  filled
                  v-model.trim="roomCodeInput"
                  label="Código de la Sala *"
                  hint="Ingresa el código de 6 caracteres de la sala."
                  lazy-rules
                  :rules="[
                    val => !!val || 'El código de sala es requerido.',
                    val => (val && val.length === 6) || 'El código debe tener 6 caracteres.'
                  ]"
                  @update:model-value="value => roomCodeInput = value.toUpperCase()"
                  maxlength="6"
                />
  
                <q-input
                  filled
                  v-model.trim="nicknameInput"
                  label="Tu Nickname (Opcional)"
                  hint="Si no ingresas uno, se usará uno por defecto."
                  maxlength="50"
                  :rules="[
                      val => (!val || val.length >= 2) || 'El nickname debe tener al menos 2 caracteres.'
                  ]"
                />
  
                <div v-if="roomStore.roomError" class="text-negative q-mb-md">
                  Error: {{ roomStore.roomError }}
                </div>
  
                <div>
                  <q-btn
                    label="Unirse a Sala"
                    type="submit"
                    color="secondary"
                    class="full-width"
                    :loading="roomStore.isLoadingRoom"
                    :disable="!roomCodeInput || roomCodeInput.length !== 6 || roomStore.isLoadingRoom"
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
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import { useRoomStore } from 'stores/room-store';
  import { Notify } from 'quasar'; // Opcional, para notificaciones directas
  
  const router = useRouter();
  const roomStore = useRoomStore();
  
  const roomCodeInput = ref('');
  const nicknameInput = ref('');
  
  onMounted(() => {
    // Limpiar errores previos de sala al entrar a la página
    roomStore.roomError = null;
  });
  
  const handleJoinRoom = async () => {
    if (!roomCodeInput.value || roomCodeInput.value.length !== 6) {
      Notify.create({ type: 'negative', message: 'Por favor, ingresa un código de sala válido de 6 caracteres.' });
      return;
    }
    if (nicknameInput.value && nicknameInput.value.length < 2) {
      Notify.create({ type: 'negative', message: 'Si ingresas un nickname, debe tener al menos 2 caracteres.'});
      return;
    }
  
    const roomDetails = {
      roomCode: roomCodeInput.value.toUpperCase(), // Enviar en mayúsculas como en el backend
      nickname: nicknameInput.value || undefined // Enviar undefined si está vacío para que el backend use el default
    };
  
    const joinedRoomData = await roomStore.joinRoom(roomDetails);
  
    if (joinedRoomData && joinedRoomData.id) {
      // Redirigir al lobby de la sala a la que se unió
      router.push({ name: 'RoomLobby', params: { roomId: joinedRoomData.id } });
    } else {
      // El error ya debería haberse mostrado a través de roomStore.roomError o una notificación desde el store.
      // Notify.create({ type: 'negative', message: roomStore.roomError || 'No se pudo unir a la sala.' });
    }
  };
  </script>
  
  <style scoped>
  .q-card {
    max-width: 500px; /* O el ancho que prefieras */
  }
  </style>