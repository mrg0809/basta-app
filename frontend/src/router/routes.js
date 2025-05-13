const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'GamePage', component: () => import('pages/GamePage.vue') } 
    ]
  },
  {
    path: '/game', // Opcional, si quieres una ruta específica además de la raíz
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/GamePage.vue') },
      {
        path: 'create-room',
        name: 'CreateRoom',
        component: () => import('pages/CreateRoomPage.vue'),
        meta: { requiresAuth: true } // Proteger esta ruta
      },
      {
        path: 'join-room',
        name: 'JoinRoom',
        component: () => import('pages/JoinRoomPage.vue'),
        meta: { requiresAuth: true } // Proteger esta ruta
      },
      {
        path: 'room/:roomId/lobby', // Usaremos roomId (UUID) como parámetro
        name: 'RoomLobby',
        component: () => import('pages/RoomLobbyPage.vue'),
        props: true, // Para pasar route.params como props al componente
        meta: { requiresAuth: true } // Proteger esta ruta
      }
      // Puedes tener una página de login dedicada si quieres
      // { path: 'login', name: 'Login', component: () => import('pages/LoginPage.vue') },
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
