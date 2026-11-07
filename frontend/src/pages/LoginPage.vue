<template>
  <q-layout>
    <q-page-container>
      <q-page class="fundo-login flex flex-center q-pa-md">
        <q-card style="width: 420px; max-width: 100%">
          <q-card-section class="text-center">
            <q-icon name="calculate" color="primary" size="48px" />
            <div class="text-h5 text-primary text-weight-bold q-mt-sm">Calculadora RSC-TAE</div>
            <div class="text-body2 text-grey-8 q-mt-xs">
              Simule sua pontuação no Reconhecimento de Saberes e Competências dos servidores
              Técnico-Administrativos em Educação.
            </div>
          </q-card-section>

          <q-card-section>
            <q-form class="q-gutter-md" @submit="entrar">
              <q-input
                v-model="email"
                outlined
                dense
                type="email"
                label="E-mail"
                autocomplete="username"
                :rules="[(v) => !!v || 'Informe o e-mail']"
              >
                <template #prepend><q-icon name="mail" /></template>
              </q-input>
              <q-input
                v-model="senha"
                outlined
                dense
                label="Senha"
                autocomplete="current-password"
                :type="mostrarSenha ? 'text' : 'password'"
                :rules="[(v) => !!v || 'Informe a senha']"
              >
                <template #prepend><q-icon name="lock" /></template>
                <template #append>
                  <q-icon
                    :name="mostrarSenha ? 'visibility' : 'visibility_off'"
                    class="cursor-pointer"
                    @click="mostrarSenha = !mostrarSenha"
                  />
                </template>
              </q-input>
              <q-btn
                type="submit"
                color="primary"
                icon="login"
                label="Entrar"
                class="full-width"
                :loading="entrando"
              />
            </q-form>
          </q-card-section>

          <!-- Usuário de teste: criado pelo seed do backend, para quem quiser experimentar. -->
          <q-card-section class="q-pt-none">
            <q-banner dense rounded class="bg-blue-1 text-grey-9">
              <template #avatar><q-icon name="info" color="primary" /></template>
              <div class="text-weight-medium">Usuário de teste</div>
              <div>E-mail: <b>{{ USUARIO_TESTE.email }}</b></div>
              <div>Senha: <b>{{ USUARIO_TESTE.senha }}</b></div>
              <q-separator class="q-my-xs" />
              <div class="text-weight-medium">Tecnologia</div>
              <div>Frontend: <b>{{ TECNOLOGIA.frontend }}</b></div>
              <div>Backend: <b>{{ TECNOLOGIA.backend }}</b></div>
              <template #action>
                <q-btn flat dense color="primary" label="Preencher" @click="preencherTeste" />
              </template>
            </q-banner>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const senha = ref('')
const mostrarSenha = ref(false)
const entrando = ref(false)

const USUARIO_TESTE = { email: 'teste@teste.com.br', senha: '123456' }

// Definidas em quasar.config.js (build.env): cada repositório informa o seu backend.
const TECNOLOGIA = {
  frontend: process.env.TECNOLOGIA_FRONTEND,
  backend: process.env.TECNOLOGIA_BACKEND,
}

function preencherTeste() {
  email.value = USUARIO_TESTE.email
  senha.value = USUARIO_TESTE.senha
}

async function entrar() {
  entrando.value = true
  try {
    await auth.login(email.value, senha.value)
    router.push({ name: 'calculadora' })
  } catch {
    // A mensagem de erro já é exibida pelo interceptor do axios.
  } finally {
    entrando.value = false
  }
}
</script>
