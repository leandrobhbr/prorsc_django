import { defineStore } from 'pinia'
import { api } from 'boot/axios'

// Uma função por endpoint da API da calculadora.
export const useRscStore = defineStore('rsc', {
  actions: {
    obterCatalogo: () => api.get('/rsc/catalogo'),
    listarRequerimentos: () => api.get('/rsc'),
    criarRequerimento: (payload) => api.post('/rsc', payload),
    obterDados: (hashid) => api.get(`/rsc/${hashid}`),
    atualizarDadosBasicos: (hashid, payload) => api.post(`/rsc/${hashid}/escolaridade`, payload),
    salvarNivelSelecionado: (hashid, nivel) =>
      api.post(`/rsc/${hashid}/nivel-selecionado`, { rsc_nivel_selecionado: nivel }),
    adicionarAtividade: (rscHashid, payload) =>
      api.post('/rsc/atividade', { rsc_hashid: rscHashid, ...payload }),
    atualizarAtividade: (hashid, payload) => api.put(`/rsc/atividade/${hashid}`, payload),
    excluirAtividade: (hashid) => api.delete(`/rsc/atividade/${hashid}`),
  },
})
