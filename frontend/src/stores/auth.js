import { defineStore } from 'pinia'
import { api } from 'boot/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    usuario: null, // { token, name, email, usu_hashid }
  }),

  getters: {
    autenticado: (state) => !!state.usuario?.token,
  },

  actions: {
    async login(email, password) {
      const { data } = await api.post('/login', { email, password }, { semAviso401: true })
      this.usuario = {
        token: data.token,
        name: data.name,
        email: data.email,
        usu_hashid: data.usu_hashid,
      }
    },

    // JWT é "stateless": sair é apenas descartar o token no navegador.
    logout() {
      this.usuario = null
    },
  },

  persist: true,
})
