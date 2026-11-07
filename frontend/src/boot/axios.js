import { defineBoot } from '#q-app/wrappers'
import axios from 'axios'
import { Notify } from 'quasar'
import { useAuthStore } from 'stores/auth'

const api = axios.create({ baseURL: process.env.API })

// Junta as mensagens de erro da API em um texto só.
// Formatos possíveis: {errors: {campo: [msg]}}, {errors: [msg]} ou {message: msg}.
export function mensagemDeErro(error) {
  const data = error?.response?.data
  if (data?.errors) {
    return Object.values(data.errors).flat().join(' ')
  }
  return data?.message || 'Não foi possível falar com o servidor.'
}

export default defineBoot(({ router, store }) => {
  const auth = useAuthStore(store)

  // Antes de cada requisição: envia o token JWT, se houver.
  api.interceptors.request.use((config) => {
    if (auth.usuario?.token) config.headers.Authorization = `Bearer ${auth.usuario.token}`
    return config
  })

  // Depois de cada resposta com erro: 401 volta para o login; os demais viram aviso.
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error.response?.status
      if (status === 401 && !error.config?.semAviso401) {
        auth.logout()
        router.push({ name: 'login' })
      } else {
        Notify.create({ type: 'negative', message: mensagemDeErro(error), position: 'top' })
      }
      return Promise.reject(error)
    },
  )
})

export { api }
