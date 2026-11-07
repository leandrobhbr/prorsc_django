<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-icon name="calculate" size="28px" class="q-mr-sm" />
        <q-toolbar-title>Calculadora RSC-TAE</q-toolbar-title>
        <span class="q-mr-md gt-xs">{{ auth.usuario?.name }}</span>
        <q-btn flat dense no-caps icon="logout" label="Sair" @click="sair" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'

const auth = useAuthStore()
const router = useRouter()

function sair() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>
