// src/stores/game-store.js
import { defineStore } from 'pinia';
import { Notify } from 'quasar';

export const useGameStore = defineStore('game', {
  state: () => ({
    gameTitle: 'BASTA Futbolera',
    gameFields: [
      { id: 'playerName', label: 'Nombre Jugador' },
      { id: 'stadiumName', label: 'Nombre Estadio' },
      { id: 'team', label: 'Equipo' },
      { id: 'nationalTeam', label: 'Selección' },
      { id: 'coach', label: 'Director Técnico' },
      { id: 'playerNickname', label: 'Apodo Jugador' },
      { id: 'thing', label: 'Cosa (fútbol)' },
    ],
    answers: {},
    scores: {},
    currentLetter: '',
    gameInProgress: false,
    gameFinished: false,
    alphabet: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  }),

  getters: {
    totalScore: (state) => {
      return Object.values(state.scores).reduce((sum, score) => sum + (score || 0), 0);
    },
    initialAnswers: (state) => {
      const initial = {};
      state.gameFields.forEach(field => {
        initial[field.id] = '';
      });
      return initial;
    }
  },

  actions: {
    initializeGameState() {
      this.answers = { ...this.initialAnswers };
      this.scores = {};
      this.currentLetter = '';
      this.gameInProgress = false;
      this.gameFinished = false;
    },

    getRandomLetter() {
      const randomIndex = Math.floor(Math.random() * this.alphabet.length);
      return this.alphabet[randomIndex];
    },

    startGame() {
      this.initializeGameState();
      this.currentLetter = this.getRandomLetter();
      this.gameInProgress = true;
      Notify.create({
        message: `¡El juego ha comenzado! Letra: ${this.currentLetter}`,
        color: 'positive',
        icon: 'play_arrow'
      });
    },

    // Acción para actualizar una respuesta específica
    updateAnswer({ fieldId, value }) {
      // Corrección aquí:
      if (Object.prototype.hasOwnProperty.call(this.answers, fieldId)) {
        this.answers[fieldId] = value;
      }
      // Alternativamente, si sabes que this.answers es un objeto simple
      // y no te preocupan las propiedades del prototipo, podrías usar:
      // if (fieldId in this.answers) {
      //   this.answers[fieldId] = value;
      // }
      // Pero `Object.prototype.hasOwnProperty.call` es la forma más segura y la que ESLint prefiere.
    },

    calculateScores() {
      let tempScores = {};
      this.gameFields.forEach(field => {
        const answer = this.answers[field.id]?.trim() || '';
        if (answer && answer.toUpperCase().startsWith(this.currentLetter)) {
          tempScores[field.id] = 100;
        } else if (answer) {
          tempScores[field.id] = 0;
        } else {
          tempScores[field.id] = 0;
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

    resetGame() {
      this.initializeGameState();
      Notify.create({
        message: 'Nuevo juego listo.',
        color: 'secondary',
        icon: 'refresh'
      });
    },
  }
});