import { defineStore } from '#q-app/wrappers'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

export default defineStore(() => {
  const pinia = createPinia()
  // Permite "persist: true" nas stores (salva no localStorage).
  pinia.use(piniaPluginPersistedstate)
  return pinia
})
