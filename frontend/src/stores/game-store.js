// src/stores/game-store.js
import { defineStore } from 'pinia';
import { Notify } from 'quasar';
import { api } from 'boot/axios'; 

export const useGameStore = defineStore('game', {
  state: () => ({
    // gameTitle: 'BASTA Futbolera', // Lo podemos generar dinámicamente o quitar
    // gameFields: [...], // Esto será reemplazado por currentCategories

    themes: [], // Para almacenar las temáticas cargadas del backend
    selectedTheme: null, // Para almacenar la temática seleccionada (objeto completo)
    currentCategories: [], // Para las categorías de la temática seleccionada

    answers: {},
    scores: {},
    currentLetter: '',
    gameInProgress: false,
    gameFinished: false,
    alphabet: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  }),

  getters: {
    gameTitle: (state) => {
      return state.selectedTheme ? `BASTA - ${state.selectedTheme.name}` : 'BASTA';
    },
    totalScore: (state) => {
      return Object.values(state.scores).reduce((sum, score) => sum + (score || 0), 0);
    },
    initialAnswers: (state) => {
      const initial = {};
      // Ahora se basa en currentCategories
      state.currentCategories.forEach(category => {
        initial[category.id] = ''; // Usaremos category.id como key para las respuestas
      });
      return initial;
    },
    // Un getter para saber si el juego está listo para empezar (temática y categorías cargadas)
    isGameSetupComplete: (state) => {
      return state.selectedTheme && state.currentCategories.length > 0;
    }
  },

  actions: {
    initializeGameState() {
      this.answers = { ...this.initialAnswers }; // Usar el getter
      this.scores = {};
      this.currentLetter = '';
      this.gameInProgress = false;
      this.gameFinished = false;
      // No reseteamos themes, selectedTheme, o currentCategories aquí,
      // ya que son parte de la configuración del juego, no del estado de una ronda.
    },

    // --- NUEVAS ACCIONES ---
    async fetchThemes() {
      try {
        const response = await api.get('/themes/'); // Usa la instancia 'api'
        this.themes = response.data;
        if (this.themes.length > 0) {
          // Opcional: seleccionar la primera temática por defecto
          // this.selectTheme(this.themes[0].id);
        }
        Notify.create({ message: 'Temáticas cargadas', color: 'positive', icon: 'style' });
      } catch (error) {
        console.error('Error fetching themes:', error);
        Notify.create({
          message: `Error al cargar temáticas: ${error.response?.data?.detail || error.message}`,
          color: 'negative',
          icon: 'error_outline'
        });
        this.themes = []; // Asegurar que themes sea un array vacío en caso de error
      }
    },

    async selectTheme(themeId) {
      if (!themeId) {
        this.selectedTheme = null;
        this.currentCategories = [];
        this.initializeGameState(); // Resetea respuestas si no hay temática
        return;
      }
      const theme = this.themes.find(t => t.id === themeId);
      if (theme) {
        this.selectedTheme = theme;
        await this.fetchCategoriesForTheme(themeId);
        this.initializeGameState(); // Resetea el estado del juego para la nueva temática
      }
    },

    async fetchCategoriesForTheme(themeId) {
      if (!themeId) {
        this.currentCategories = [];
        return;
      }
      try {
        // El endpoint es /categories/?theme_id=<uuid>
        const response = await api.get(`/categories/?theme_id=${themeId}`);
        this.currentCategories = response.data;
        Notify.create({ message: `Categorías para '${this.selectedTheme?.name}' cargadas.`, color: 'info' });
      } catch (error) {
        console.error('Error fetching categories:', error);
        Notify.create({
          message: `Error al cargar categorías: ${error.response?.data?.detail || error.message}`,
          color: 'negative'
        });
        this.currentCategories = []; // Asegurar que categories sea un array vacío en caso de error
      }
    },
    // --- FIN NUEVAS ACCIONES ---

    getRandomLetter() {
      const randomIndex = Math.floor(Math.random() * this.alphabet.length);
      return this.alphabet[randomIndex];
    },

    startGame() {
      if (!this.isGameSetupComplete) {
        Notify.create({ message: 'Por favor, selecciona una temática primero.', color: 'warning' });
        return;
      }
      this.initializeGameState(); // Asegura que answers y scores estén limpios para las currentCategories
      this.currentLetter = this.getRandomLetter();
      this.gameInProgress = true;
      Notify.create({
        message: `¡Juego iniciado! Letra: ${this.currentLetter} | Temática: ${this.selectedTheme.name}`,
        color: 'positive',
        icon: 'play_arrow'
      });
    },

    updateAnswer({ categoryId, value }) { // Ahora usamos categoryId
      if (Object.prototype.hasOwnProperty.call(this.answers, categoryId)) {
        this.answers[categoryId] = value;
      } else {
        // Opcional: si la categoryId no existe en answers (lo que no debería pasar
        // si initialAnswers se genera correctamente), podrías querer añadirla o loguear un warning.
        // Por ahora, simplemente la ignoramos si no existe, pero lo ideal es que siempre exista.
        // console.warn(`Category ID ${categoryId} not found in answers object. InitialAnswers might be incorrect.`);
        // O, si quieres que siempre se cree si no existe (aunque esto puede ocultar problemas en initialAnswers):
        this.answers[categoryId] = value;
      }
    },

    calculateScores() {
      let tempScores = {};
      this.currentCategories.forEach(category => {
        const answer = this.answers[category.id]?.trim() || '';
        if (answer && answer.toUpperCase().startsWith(this.currentLetter)) {
          tempScores[category.id] = 100;
        } else if (answer) {
          tempScores[category.id] = 0;
        } else {
          tempScores[category.id] = 0;
        }
      });
      this.scores = tempScores;
    },

    submitBasta() {
      if (!this.gameInProgress) return;
      this.gameInProgress = false;
      this.gameFinished = true;
      this.calculateScores();
      Notify.create({
        message: '¡BASTA! Revisando respuestas...',
        color: 'info',
        icon: 'check_circle'
      });
    },

    resetGame() { // Ahora resetea manteniendo la temática seleccionada
      this.initializeGameState(); // Limpia respuestas, scores, letra, estado de juego
      // this.selectedTheme = null; // Opcional: si quieres que se deseleccione la temática
      // this.currentCategories = [];
      Notify.create({
        message: 'Nuevo juego listo con la misma temática.',
        color: 'secondary',
        icon: 'refresh'
      });
    },
  }
});