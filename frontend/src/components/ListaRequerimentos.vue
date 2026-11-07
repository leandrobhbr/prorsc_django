<template>
  <div>
    <div class="row items-center q-mb-md">
      <div class="text-h6 text-grey-9">Meus cálculos</div>
      <q-space />
      <q-btn
        unelevated
        no-caps
        color="primary"
        icon="add"
        label="Novo cálculo"
        :loading="criando"
        @click="$emit('novo')"
      />
    </div>

    <div v-if="lista.length === 0" class="text-center text-grey-6 q-py-xl">
      <q-icon name="calculate" size="56px" /><br />
      Nenhum cálculo ainda. Clique em "Novo cálculo" para começar.
    </div>

    <q-list v-else bordered separator class="rounded-borders bg-white">
      <q-item v-for="req in lista" :key="req.rsc_hashid" clickable @click="$emit('abrir', req)">
        <q-item-section avatar>
          <q-avatar color="primary" text-color="white" icon="description" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-weight-medium">
            {{ rotuloEscolaridade(req.rsc_escolaridade) }}
            <span v-if="req.rsc_nivel_selecionado" class="text-grey-7">
              · pleiteia {{ req.rsc_nivel_selecionado }}
            </span>
          </q-item-label>
          <q-item-label caption>
            {{ req.atividades_count }} {{ req.atividades_count === 1 ? 'atividade' : 'atividades' }}
            · {{ formatarPontos(req.total_pontos) }} pontos · atualizado em {{ req.updated_at }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-chip
            dense
            :color="req.melhor_nivel ? 'green-2' : 'grey-3'"
            :text-color="req.melhor_nivel ? 'green-10' : 'grey-8'"
            :icon="req.melhor_nivel ? 'check_circle' : 'hourglass_empty'"
          >
            {{ req.melhor_nivel || 'Nenhum nível atingido' }}
          </q-chip>
        </q-item-section>
      </q-item>
    </q-list>
  </div>
</template>

<script setup>
import { formatarPontos, rotuloEscolaridade } from 'src/utils/rsc'

defineProps({
  lista: { type: Array, default: () => [] },
  criando: { type: Boolean, default: false },
})

defineEmits(['novo', 'abrir'])
</script>
