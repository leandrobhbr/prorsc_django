import { defineRouter } from '#q-app/wrappers'
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from 'stores/auth'
import routes from './routes'

export default defineRouter(({ store }) => {
  const router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createWebHashHistory(),
  })

  // Guarda de navegação: páginas com "requerLogin" exigem usuário autenticado.
  router.beforeEach((to) => {
    const auth = useAuthStore(store)
    if (to.meta.requerLogin && !auth.autenticado) return { name: 'login' }
    if (to.name === 'login' && auth.autenticado) return { name: 'calculadora' }
  })

  return router
})
