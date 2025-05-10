// src/stores/auth-store.js
import { defineStore } from 'pinia';
import { supabase } from 'boot/supabase-client';
// import { Notify } from 'quasar'; // Comentado temporalmente para depuración

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        session: null,
        loading: true,
        justSignedIn: false,
        initialCheckDone: false,
      }),
    
      getters: {
        isAuthenticated: (state) => {
          // console.log('AuthStore Getter: isAuthenticated called, user is:', state.user); // Log opcional para depurar el getter
          return !!state.user;
        },
        // ... otros getters ...
      },
    
      actions: {
        _setUserSession(session) {
          const previousUser = this.user;
          console.log('AuthStore Action: _setUserSession - Entrando. Sesión recibida:', session ? 'Sí' : 'No', 'Usuario anterior:', previousUser ? previousUser.id : 'ninguno');
          if (session) {
            this.session = session;
            this.user = session.user;
            console.log('AuthStore Action: _setUserSession - Usuario establecido:', this.user ? this.user.id : 'error al establecer');
          } else {
            this.session = null;
            this.user = null;
            console.log('AuthStore Action: _setUserSession - Usuario establecido en null');
          }
    
          if (!previousUser && this.user) {
            console.log('AuthStore Action: _setUserSession - justSignedIn establecido en true');
            this.justSignedIn = true;
          } else if (previousUser && !this.user) {
            // Esto podría ocurrir si se cierra sesión pero justSignedIn ya era false
            // No necesitamos cambiar justSignedIn aquí usualmente
          }
        },
    
        initializeAuthListener() {
          console.log('AuthStore Action: initializeAuthListener - Configurando listener...');
          supabase.auth.onAuthStateChange((event, session) => {
            console.log('AuthStore Event: onAuthStateChange - Evento:', event, 'Sesión:', session ? 'Sí' : 'No');
            this._setUserSession(session); // Llama a la acción actualizada
    
            if (event === 'SIGNED_IN' && this.justSignedIn) {
              console.log(`AuthStore Event: SIGNED_IN (justSignedIn) - Bienvenido, ${this.userName || this.userEmail}!`);
            } else if (event === 'SIGNED_OUT') {
              console.log('AuthStore Event: SIGNED_OUT - Has cerrado sesión.');
            } else if (event === 'INITIAL_SESSION') {
              console.log('AuthStore Event: INITIAL_SESSION procesada.');
            } else if (event === 'USER_UPDATED') {
                console.log('AuthStore Event: USER_UPDATED.');
            } else if (event === 'TOKEN_REFRESHED') {
                console.log('AuthStore Event: TOKEN_REFRESHED.');
            }
          });
        },
    
        clearJustSignedInFlag() {
          console.log('AuthStore Action: clearJustSignedInFlag');
          this.justSignedIn = false;
        },
    
        async signInWithGoogle() {
          // La guarda para isAuthenticated ya está aquí, es importante que isAuthenticated sea fiable.
          if (this.isAuthenticated) {
            console.warn('AuthStore Action: signInWithGoogle - Intento abortado, usuario ya autenticado.');
            this.loading = false;
            // Quizás notificar al usuario que ya está logueado, o simplemente no hacer nada.
            // Es posible que la UI deba actualizarse más rápido para ocultar el botón de login.
            return;
          }
          console.log('AuthStore Action: signInWithGoogle - Iniciando flujo OAuth...');
          this.loading = true;
          try {
            const oauthResponse = await supabase.auth.signInWithOAuth({
              provider: 'google',
              options: {
                redirectTo: window.location.origin,
              },
            });
            if (oauthResponse.error) {
              throw oauthResponse.error;
            }
            // La redirección a Google ocurrirá, la consola no mostrará mucho más aquí
            console.log('AuthStore Action: signInWithGoogle - Redirección a Google iniciada (o debería).');
          } catch (error) {
            console.error('Error signing in with Google:', error);
          } finally {
            this.loading = false;
          }
        },
    
        async signOut() {
          console.log('AuthStore Action: signOut - Iniciando...');
          this.loading = true;
          try {
            const { error } = await supabase.auth.signOut();
            if (error) {
              console.error('Error devuelto por supabase.auth.signOut:', error);
              throw error;
            }
            console.log('AuthStore Action: signOut - Completado exitosamente (evento SIGNED_OUT lo manejará).');
          } catch (error) {
            console.error('Error procesando el cierre de sesión:', error);
          } finally {
            this.loading = false;
            this.initialCheckDone = true;
          }
        },
    
        async fetchCurrentSession() {
          this.loading = true;
          this.initialCheckDone = false; // Resetear por si se llama múltiples veces (aunque no debería)
          try {
            console.log('AuthStore Action: fetchCurrentSession - Iniciando fetch...');
            const { data: { session }, error } = await supabase.auth.getSession();
    
            if (error) {
              console.error('AuthStore Action: fetchCurrentSession - Error obteniendo sesión:', error.message);
              this._setUserSession(null);
            } else {
              console.log('AuthStore Action: fetchCurrentSession - Sesión obtenida de Supabase:', session ? `Sí, usuario ${session.user.id}` : 'No');
              this._setUserSession(session);
            }
          } catch (e) {
            console.error('AuthStore Action: fetchCurrentSession - Excepción inesperada:', e);
            this._setUserSession(null);
          } finally {
            this.loading = false;
            this.initialCheckDone = true;
            console.log(`AuthStore Action: fetchCurrentSession - Finalizado. loading: ${this.loading}, initialCheckDone: ${this.initialCheckDone}, isAuthenticated: ${this.isAuthenticated}`);
          }
        }
      },
    });