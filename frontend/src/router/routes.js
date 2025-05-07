const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      // Comenta o elimina la ruta por defecto a IndexPage si quieres que GamePage sea la principal por ahora
      // { path: '', component: () => import('pages/IndexPage.vue') },
      { path: '', component: () => import('pages/GamePage.vue') } // Nueva ruta principal
    ]
  },
  {
    path: '/game', // Opcional, si quieres una ruta específica además de la raíz
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/GamePage.vue') }
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
