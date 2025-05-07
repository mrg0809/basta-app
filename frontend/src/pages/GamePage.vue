<template>
    <q-page padding>
      <div class="q-pa-md">
        <div class="text-h4 q-mb-md text-center">{{ gameStore.gameTitle }}</div>
  
        <div class="row q-mb-md items-center">
          <q-btn
            @click="gameStore.startGame"
            label="¡Iniciar Juego!"
            color="primary"
            class="q-mr-md"
            :disable="gameStore.gameInProgress"
          />
          <div v-if="gameStore.currentLetter" class="text-h6">Letra: {{ gameStore.currentLetter }}</div>
        </div>
  
        <q-form @submit.prevent="handleFormSubmit">
          <div v-for="field in gameStore.gameFields" :key="field.id" class="q-mb-sm">
            <q-input
              filled
              :model-value="gameStore.answers[field.id]"
              @update:model-value="value => gameStore.updateAnswer({ fieldId: field.id, value })"
              :label="field.label"
              :disable="!gameStore.gameInProgress || gameStore.gameFinished"
              bottom-slots
              dense
            >
              <template v-if="gameStore.scores[field.id] !== undefined && gameStore.gameFinished" v-slot:append>
                <q-badge :color="getScoreColor(gameStore.scores[field.id])">
                  {{ gameStore.scores[field.id] }}
                </q-badge>
              </template>
            </q-input>
          </div>
  
          <q-btn
            label="¡BASTA!"
            type="submit"
            color="negative"
            class="q-mt-md full-width"
            :disable="!gameStore.gameInProgress || gameStore.gameFinished"
          />
        </q-form>
  
        <div v-if="gameStore.gameFinished" class="q-mt-lg text-center">
          <div class="text-h5">Juego Terminado</div>
          <div class="text-h6">Puntaje Total: {{ gameStore.totalScore }}</div>
          <q-btn
            @click="gameStore.resetGame"
            label="Jugar de Nuevo"
            color="secondary"
            class="q-mt-md"
          />
        </div>
      </div>
    </q-page>
  </template>
  
  <script setup>
  import { onMounted } from 'vue';
  import { useGameStore } from '../stores/game-store'; // Importa el store
  // Quasar $q ya no es necesario aquí para notificaciones si se manejan en el store
  // import { useQuasar } from 'quasar';
  
  // const $q = useQuasar(); // Ya no es necesario si las notificaciones están en el store
  const gameStore = useGameStore(); // Obtén la instancia del store
  
  // Inicializar el estado del juego cuando el componente se monta por primera vez
  // o si quieres que siempre se resetee al cargar la página.
  onMounted(() => {
    if (!gameStore.gameInProgress && !gameStore.gameFinished) {
      gameStore.initializeGameState();
    }
  });
  
  const handleFormSubmit = () => {
    gameStore.submitBasta();
  };
  
  const getScoreColor = (score) => {
    if (score === 100) return 'positive';
    if (score === 50) return 'warning'; // Para futuras validaciones de respuestas repetidas
    return 'negative';
  };
  
  </script>
  
  <style lang="scss" scoped>
  .text-h4, .text-h5, .text-h6 {
    color: $primary;
  }
  </style>