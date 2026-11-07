const routes = [
  {
    path: '/',
    name: 'login',
    component: () => import('pages/LoginPage.vue'),
  },
  {
    path: '/calculadora',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requerLogin: true },
    children: [
      { path: '', name: 'calculadora', component: () => import('pages/CalculadoraPage.vue') },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    redirect: { name: 'login' },
  },
]

export default routes
