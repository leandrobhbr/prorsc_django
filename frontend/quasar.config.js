// Configuração do Quasar (https://quasar.dev/quasar-cli-vite/quasar-config-file)
import { defineConfig } from '#q-app/wrappers'

// URL da API: venha da variável API_URL ou use o backend local desta implementação.
const API_PADRAO = 'http://localhost:8003/api/v1'

// Tecnologias exibidas na tela de login.
const TECNOLOGIA_FRONTEND = 'Vue 3 + Quasar'
const TECNOLOGIA_BACKEND = 'Python + Django REST Framework'

export default defineConfig(() => ({
  boot: ['axios'],

  css: ['app.scss'],

  extras: ['roboto-font', 'material-icons'],

  build: {
    target: {
      browser: ['es2022', 'firefox115', 'chrome115', 'safari14'],
      node: 'node20',
    },
    vueRouterMode: 'hash',
    // Pasta onde o site fica publicado. Raiz do domínio: "/" (padrão).
    // Em subpasta: PUBLIC_PATH=/prorsc_django/ no momento do build.
    publicPath: process.env.PUBLIC_PATH || '/',
    env: {
      API: process.env.API_URL || API_PADRAO,
      TECNOLOGIA_FRONTEND,
      TECNOLOGIA_BACKEND,
    },
  },

  devServer: {
    port: Number(process.env.FRONT_PORT || 9001),
    open: false,
  },

  framework: {
    lang: 'pt-BR',
    plugins: ['Notify', 'Dialog'],
  },
}))
