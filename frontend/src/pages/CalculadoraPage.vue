<!--
  Calculadora RSC-TAE de livre acesso — derivada do ProRSC-TAE (Software Público Brasileiro).
  Licenciado sob a GNU General Public License v2.0 ou posterior (GPL-2.0-or-later).
-->
<template>
  <q-page padding class="bg-grey-2">
    <div style="max-width: 1000px; margin: 0 auto">
      <div v-if="carregando" class="flex flex-center q-py-xl">
        <q-spinner color="primary" size="40px" />
      </div>

      <!-- Lista de cálculos -->
      <ListaRequerimentos
        v-else-if="!ativo"
        :lista="lista"
        :criando="criando"
        @novo="novoCalculo"
        @abrir="(req) => abrir(req.rsc_hashid)"
      />

      <!-- Cálculo aberto -->
      <template v-else>
        <q-btn flat no-caps icon="arrow_back" label="Meus cálculos" class="q-mb-sm" @click="voltar" />

        <q-card flat bordered class="q-mb-md">
          <q-card-section class="row q-col-gutter-md items-center">
            <div class="col-12 col-sm-6">
              <q-input
                v-model="ativo.rsc_nome_servidor"
                outlined
                dense
                label="Nome do servidor (opcional)"
                :readonly="!editavel"
                @change="salvarDadosBasicos"
              />
            </div>
            <div class="col-12 col-sm-6">
              <q-select
                v-model="ativo.rsc_escolaridade"
                :options="ESCOLARIDADES"
                emit-value
                map-options
                outlined
                dense
                label="Escolaridade atual"
                :readonly="!editavel"
                @update:model-value="salvarDadosBasicos"
              />
            </div>
          </q-card-section>
          <q-banner v-if="ativo.rsc_escolaridade === 'doutorado'" class="bg-green-1 text-green-10">
            <template #avatar><q-icon name="emoji_events" color="green-8" /></template>
            O RSC-TAE é destinado a servidores com escolaridade inferior ao doutorado.
          </q-banner>
        </q-card>

        <PainelResultado
          class="painel-fixo q-mb-md"
          :calculos="calculos"
          :nivel-selecionado="ativo.rsc_nivel_selecionado"
        />

        <!-- Atividades por requisito -->
        <q-card v-for="req in REQUISITOS" :key="req.id" flat bordered class="q-mb-sm">
          <q-expansion-item default-opened header-class="bg-blue-1">
            <template #header>
              <q-item-section avatar><q-icon :name="req.icon" :color="req.color" /></q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">
                  Requisito {{ req.id }} — {{ req.titulo }}
                </q-item-label>
                <q-item-label caption>
                  {{ formatarPontos(calculos.pontos_por_requisito?.[req.id]) }} pontos ·
                  {{ calculos.criterios_por_requisito?.[req.id] || 0 }} atividade(s)
                </q-item-label>
              </q-item-section>
              <q-item-section v-if="editavel" side>
                <q-btn flat round dense icon="add" color="primary" @click.stop="dialog.abrirAdicionar(req.id)" />
              </q-item-section>
            </template>

            <q-card-section class="q-pt-sm">
              <div class="text-caption text-grey-7 q-mb-sm">{{ req.descricao }}</div>
              <div v-if="porRequisito(req.id).length === 0" class="text-grey-6 text-center q-py-sm">
                Nenhuma atividade neste requisito.
              </div>
              <q-list v-else separator>
                <q-item v-for="ati in porRequisito(req.id)" :key="ati.rsa_hashid">
                  <q-item-section>
                    <q-item-label>{{ ati.rsa_descricao }}</q-item-label>
                    <q-item-label caption>
                      <q-badge color="blue-1" text-color="blue-10">{{ formatarPontos(ati.rsa_pontos) }} pts</q-badge>
                      <span class="q-ml-xs">{{ ati.rsa_observacoes }}</span>
                    </q-item-label>
                  </q-item-section>
                  <q-item-section v-if="editavel" side>
                    <div class="row no-wrap">
                      <q-btn flat round dense icon="edit" color="primary" @click="dialog.abrirEditar(ati)" />
                      <q-btn flat round dense icon="delete" color="negative" @click="excluir(ati)" />
                    </div>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>
          </q-expansion-item>
        </q-card>

        <DialogAtividade
          ref="dialog"
          :rsc-hashid="ativo.rsc_hashid"
          :catalogo="catalogo"
          :atividades="ativo.atividades"
          @salvo="aoSalvarAtividade"
        />
      </template>
    </div>
  </q-page>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useQuasar } from 'quasar'
import { useRscStore } from 'stores/rsc'
import DialogAtividade from 'components/DialogAtividade.vue'
import ListaRequerimentos from 'components/ListaRequerimentos.vue'
import PainelResultado from 'components/PainelResultado.vue'
import {
  ESCOLARIDADES,
  NIVEL_INDICADO_POR_ESCOLARIDADE,
  REQUISITOS,
  formatarPontos,
} from 'src/utils/rsc'

const $q = useQuasar()
const rsc = useRscStore()

const carregando = ref(true)
const criando = ref(false)
const lista = ref([])
const catalogo = ref({})
const ativo = ref(null) // requerimento aberto (resposta de GET /rsc/{hashid})
const calculos = ref({})
const dialog = ref(null)

const editavel = computed(() => ['rascunho', 'pendente'].includes(ativo.value?.rsc_status))
const porRequisito = (id) => (ativo.value?.atividades || []).filter((a) => a.rsa_requisito === id)

async function carregarLista() {
  carregando.value = true
  try {
    const [resLista, resCatalogo] = await Promise.all([rsc.listarRequerimentos(), rsc.obterCatalogo()])
    lista.value = resLista.data
    catalogo.value = resCatalogo.data
  } finally {
    carregando.value = false
  }
}

async function abrir(hashid) {
  const { data } = await rsc.obterDados(hashid)
  ativo.value = data
  calculos.value = data.calculos
  await garantirNivelIndicado()
}

async function recarregar() {
  await abrir(ativo.value.rsc_hashid)
}

// A resposta já traz o resultado recalculado: mostra na hora e depois atualiza a lista.
async function aoSalvarAtividade(novosCalculos) {
  if (novosCalculos) calculos.value = novosCalculos
  await recarregar()
}

// O nível pleiteado é o indicado para a escolaridade; o backend valida a regra.
async function garantirNivelIndicado() {
  const indicado = NIVEL_INDICADO_POR_ESCOLARIDADE[ativo.value.rsc_escolaridade]
  if (!editavel.value || !indicado || ativo.value.rsc_nivel_selecionado === indicado) return
  await rsc.salvarNivelSelecionado(ativo.value.rsc_hashid, indicado)
  ativo.value.rsc_nivel_selecionado = indicado
}

async function novoCalculo() {
  criando.value = true
  try {
    const { data } = await rsc.criarRequerimento({ rsc_escolaridade: 'graduacao' })
    await abrir(data.rsc_hashid)
  } finally {
    criando.value = false
  }
}

async function salvarDadosBasicos() {
  const { data } = await rsc.atualizarDadosBasicos(ativo.value.rsc_hashid, {
    rsc_escolaridade: ativo.value.rsc_escolaridade,
    rsc_nome_servidor: ativo.value.rsc_nome_servidor,
  })
  calculos.value = data.calculos
  await garantirNivelIndicado()
}

function excluir(atividade) {
  $q.dialog({
    title: 'Remover atividade?',
    message: atividade.rsa_descricao,
    cancel: { flat: true, label: 'Cancelar', noCaps: true },
    ok: { color: 'negative', label: 'Remover', noCaps: true },
  }).onOk(async () => {
    const { data } = await rsc.excluirAtividade(atividade.rsa_hashid)
    await aoSalvarAtividade(data.calculos)
  })
}

async function voltar() {
  ativo.value = null
  await carregarLista()
}

onMounted(carregarLista)
</script>
