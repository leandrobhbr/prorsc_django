<template>
  <q-card flat bordered class="bg-white">
    <q-card-section class="q-pb-sm">
      <div class="row items-center q-col-gutter-md">
        <div class="col-6 col-sm-3 text-center">
          <div class="text-caption text-grey-7">Pontos</div>
          <div class="text-h5 text-primary text-weight-bold">
            {{ formatarPontos(calculos.total_pontos) }}
          </div>
        </div>
        <div class="col-6 col-sm-3 text-center">
          <div class="text-caption text-grey-7">Atividades (critérios)</div>
          <div class="text-h5 text-primary text-weight-bold">{{ calculos.total_criterios || 0 }}</div>
        </div>
        <div class="col-6 col-sm-3 text-center">
          <div class="text-caption text-grey-7">Melhor nível atingido</div>
          <div class="text-h6" :class="calculos.melhor_nivel ? 'text-positive' : 'text-grey-6'">
            {{ calculos.melhor_nivel || '—' }}
          </div>
        </div>
        <div class="col-6 col-sm-3 text-center">
          <div class="text-caption text-grey-7">Próximo nível</div>
          <div class="text-h6 text-grey-8">{{ calculos.proximo_nivel || '—' }}</div>
        </div>
      </div>
    </q-card-section>

    <template v-if="nivel">
      <q-separator />
      <q-card-section>
        <div class="row items-center q-mb-sm">
          <div class="text-subtitle2">
            Nível pleiteado: {{ nivel.nivel }} ({{ nivel.label_curto }}) — equivalente a
            {{ nivel.equivalente }}
          </div>
          <q-space />
          <q-chip
            dense
            :color="nivel.atingido ? 'green-2' : 'red-1'"
            :text-color="nivel.atingido ? 'green-10' : 'red-9'"
            :icon="nivel.atingido ? 'check_circle' : 'cancel'"
          >
            {{ nivel.atingido ? 'Atendido' : 'Não atendido' }}
          </q-chip>
        </div>

        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-6">
            <div class="flex justify-between text-caption text-grey-8">
              <span>Pontuação</span>
              <span>{{ formatarPontos(calculos.total_pontos) }} / {{ nivel.pontos_minimos }}</span>
            </div>
            <q-linear-progress rounded size="8px" :value="progresso(calculos.total_pontos, nivel.pontos_minimos)" />
          </div>
          <div class="col-12 col-sm-6">
            <div class="flex justify-between text-caption text-grey-8">
              <span>Atividades</span>
              <span>{{ calculos.total_criterios }} / {{ nivel.criterios_minimos }}</span>
            </div>
            <q-linear-progress
              rounded
              size="8px"
              color="secondary"
              :value="progresso(calculos.total_criterios, nivel.criterios_minimos)"
            />
          </div>
        </div>

        <div
          v-if="nivel.req_obrigatorio.length"
          class="q-mt-sm text-caption"
          :class="nivel.req_obrigatorio_ok ? 'text-positive' : 'text-negative'"
        >
          <q-icon :name="nivel.req_obrigatorio_ok ? 'check_circle' : 'cancel'" />
          Exige pontuação em pelo menos um dos requisitos: {{ nivel.req_obrigatorio.join(', ') }}
        </div>
        <div class="q-mt-sm text-caption text-grey-7">
          <q-icon name="info" /> {{ nivel.atencao }}
        </div>
      </q-card-section>
    </template>
  </q-card>
</template>

<script setup>
import { computed } from 'vue'
import { formatarPontos } from 'src/utils/rsc'

const props = defineProps({
  calculos: { type: Object, default: () => ({}) },
  nivelSelecionado: { type: String, default: null },
})

const nivel = computed(() => props.calculos?.niveis?.[props.nivelSelecionado] || null)

const progresso = (valor, minimo) => Math.min((Number(valor) || 0) / minimo, 1)
</script>
