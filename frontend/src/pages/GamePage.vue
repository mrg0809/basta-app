<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="text-h4 q-mb-md text-center">{{ gameStore.gameTitle }}</div>

      <q-select
        filled
        v-model="selectedThemeId"
        :options="themeOptions"
        label="Selecciona una Temática"
        emit-value
        map-options
        class="q-mb-md"
        :disable="gameStore.gameInProgress || gameStore.gameFinished"
        @update:model-value="handleThemeSelection"
      />

      <div class="row q-mb-md items-center">
        <q-btn
          @click="gameStore.startGame"
          label="¡Iniciar Juego!"
          color="primary"
          class="q-mr-md"
          :disable="!gameStore.isGameSetupComplete || gameStore.gameInProgress"
        />
        <div v-if="gameStore.currentLetter" class="text-h6">Letra: {{ gameStore.currentLetter }}</div>
      </div>

      <q-form @submit.prevent="handleFormSubmit" v-if="gameStore.isGameSetupComplete">
        <div v-for="category in gameStore.currentCategories" :key="category.id" class="q-mb-sm">
          <q-input
            filled
            :model-value="gameStore.answers[category.id]"
            @update:model-value="value => gameStore.updateAnswer({ categoryId: category.id, value })"
            :label="category.name"
            :disable="!gameStore.gameInProgress || gameStore.gameFinished"
            bottom-slots
            dense
          >
            <template v-if="gameStore.scores[category.id] !== undefined && gameStore.gameFinished" v-slot:append>
              <q-badge :color="getScoreColor(gameStore.scores[category.id])">
                {{ gameStore.scores[category.id] }}
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
      <div v-else-if="gameStore.themes.length > 0 && !gameStore.selectedTheme" class="text-center q-my-md">
        <p>Por favor, selecciona una temática para ver las categorías.</p>
      </div>
       <div v-else-if="gameStore.themes.length === 0 && !loadingThemes" class="text-center q-my-md">
        <p>No hay temáticas disponibles. ¿El backend está funcionando?</p>
      </div>
      <div v-if="loadingThemes" class="text-center q-my-md">
        <q-spinner color="primary" size="3em" />
        <p>Cargando temáticas...</p>
      </div>


      <div v-if="gameStore.gameFinished && gameStore.isGameSetupComplete" class="q-mt-lg text-center">
        <div class="text-h5">Juego Terminado</div>
        <div class="text-h6">Puntaje Total: {{ gameStore.totalScore }}</div>
        <q-btn
          @click="gameStore.resetGame"
          label="Jugar de Nuevo (misma temática)"
          color="secondary"
          class="q-mt-md"
        />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useGameStore } from 'stores/game-store';

const gameStore = useGameStore();
const selectedThemeId = ref(null); // Para el v-model del q-select
const loadingThemes = ref(true);

// Opciones para q-select, mapeando las temáticas del store
const themeOptions = computed(() => {
  if (!gameStore.themes || gameStore.themes.length === 0) {
    return [];
  }
  return gameStore.themes.map(theme => ({
    label: theme.name,
    value: theme.id
  }));
});

onMounted(async () => {
  loadingThemes.value = true;
  await gameStore.fetchThemes();
  loadingThemes.value = false;
  // Si hay un tema seleccionado en el store (ej. al recargar), actualizar el q-select
  if (gameStore.selectedTheme) {
    selectedThemeId.value = gameStore.selectedTheme.id;
  }
});

const handleThemeSelection = (themeId) => {
  gameStore.selectTheme(themeId);
};

const handleFormSubmit = () => {
  gameStore.submitBasta();
};

const getScoreColor = (score) => {
  if (score === 100) return 'positive';
  if (score === 50) return 'warning';
  return 'negative';
};
</script>

<style lang="scss" scoped>
.text-h4, .text-h5, .text-h6 {
  color: $primary;
}
</style>