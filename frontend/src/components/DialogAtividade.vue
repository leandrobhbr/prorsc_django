<!--
  Calculadora RSC-TAE de livre acesso — derivada do ProRSC-TAE (Software Público Brasileiro).
  Licenciado sob a GNU General Public License v2.0 ou posterior (GPL-2.0-or-later).
-->
<template>
  <q-dialog v-model="aberto" persistent>
    <q-card style="width: 680px; max-width: 96vw">
      <q-card-section class="bg-primary text-white q-pb-sm">
        <div class="text-h6">{{ editando ? 'Editar' : 'Adicionar' }} atividade</div>
        <div class="text-caption">Requisito {{ requisito?.id }} — {{ requisito?.titulo }}</div>
      </q-card-section>

      <!-- Adicionar: escolhe um item do catálogo e informa a quantidade -->
      <template v-if="!editando">
        <q-card-section class="q-pb-none">
          <q-input
            v-model="busca"
            dense
            outlined
            clearable
            autofocus
            debounce="200"
            placeholder="Buscar no catálogo…"
          >
            <template #prepend><q-icon name="search" /></template>
          </q-input>
        </q-card-section>

        <q-scroll-area style="height: 300px">
          <q-list separator>
            <q-item
              v-for="item in itensFiltrados"
              :key="item.item_numero"
              clickable
              :disable="jaAdicionado(item)"
              :class="{ 'bg-blue-1': item.item_numero === selecionado?.item_numero }"
              @click="selecionado = item"
            >
              <q-item-section avatar>
                <q-badge color="primary" :label="item.item_numero" />
              </q-item-section>
              <q-item-section>
                <q-item-label style="white-space: normal">{{ item.item_descricao }}</q-item-label>
                <q-item-label caption>
                  {{ item.item_unidade }} · <strong>{{ item.item_pontos_unidade }} pt/un</strong>
                  <span v-if="jaAdicionado(item)" class="text-orange-8"> · já adicionado</span>
                </q-item-label>
              </q-item-section>
            </q-item>
            <q-item v-if="itensFiltrados.length === 0">
              <q-item-section class="text-grey-6 text-center">Nenhum item encontrado.</q-item-section>
            </q-item>
          </q-list>
        </q-scroll-area>

        <q-card-section v-if="selecionado" class="bg-grey-1">
          <div class="row q-col-gutter-sm items-center">
            <div class="col-12 col-sm-5">
              <q-input
                v-model.number="quantidade"
                outlined
                dense
                type="number"
                min="1"
                :label="`Quantidade (${selecionado.item_unidade})`"
              />
            </div>
            <div class="col text-body1">
              × {{ selecionado.item_pontos_unidade }} =
              <strong class="text-h6 text-primary">{{ pontos }}</strong> pontos
            </div>
            <div class="col-12">
              <q-input v-model="observacao" outlined dense label="Observação (opcional)" />
            </div>
          </div>
        </q-card-section>
      </template>

      <!-- Editar: ajusta apenas a quantidade -->
      <q-card-section v-else>
        <div class="text-body2 q-mb-md">{{ edicao.descricaoBase }}</div>
        <div class="row q-col-gutter-sm items-center">
          <div class="col-12 col-sm-5">
            <q-input
              v-model.number="quantidade"
              outlined
              dense
              type="number"
              min="1"
              :label="`Quantidade (${edicao.unidade || 'unidades'})`"
            />
          </div>
          <div class="col text-body1">
            × {{ edicao.pontosUnidade }} =
            <strong class="text-h6 text-primary">{{ pontos }}</strong> pontos
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="right" class="q-pa-md">
        <q-btn flat no-caps label="Cancelar" @click="aberto = false" />
        <q-btn
          unelevated
          no-caps
          color="primary"
          :icon="editando ? 'save' : 'add'"
          :label="editando ? 'Salvar' : 'Adicionar'"
          :loading="salvando"
          :disable="!podeSalvar"
          @click="salvar"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Notify } from 'quasar'
import { useRscStore } from 'stores/rsc'
import { REQUISITOS } from 'src/utils/rsc'

const props = defineProps({
  rscHashid: { type: String, required: true },
  catalogo: { type: Object, default: () => ({}) },
  atividades: { type: Array, default: () => [] },
})
const emit = defineEmits(['salvo'])

const rsc = useRscStore()

const aberto = ref(false)
const editando = ref(false)
const salvando = ref(false)
const requisitoId = ref('I')
const busca = ref('')
const selecionado = ref(null)
const quantidade = ref(1)
const observacao = ref('')
const edicao = ref({})

const requisito = computed(() => REQUISITOS.find((r) => r.id === requisitoId.value))

const itensFiltrados = computed(() => {
  const itens = props.catalogo[requisitoId.value] || []
  const termo = (busca.value || '').toLowerCase().trim()
  return termo ? itens.filter((i) => i.item_descricao.toLowerCase().includes(termo)) : itens
})

const pontosUnidade = computed(() =>
  editando.value ? edicao.value.pontosUnidade : selecionado.value?.item_pontos_unidade || 0,
)
const pontos = computed(() => Math.round((quantidade.value || 0) * pontosUnidade.value * 100) / 100)
const podeSalvar = computed(() => quantidade.value > 0 && (editando.value || !!selecionado.value))

// O número do item fica gravado no início das observações ("Item nº 12 · ...").
const jaAdicionado = (item) =>
  props.atividades.some(
    (a) =>
      a.rsa_requisito === requisitoId.value &&
      (a.rsa_observacoes || '').startsWith(`Item nº ${item.item_numero} `),
  )

function abrirAdicionar(reqId) {
  editando.value = false
  requisitoId.value = reqId
  busca.value = ''
  selecionado.value = null
  quantidade.value = 1
  observacao.value = ''
  aberto.value = true
}

function abrirEditar(atividade) {
  // Descrição no formato "Texto do item (3 Por ano)" → separa texto, quantidade e unidade.
  const m = (atividade.rsa_descricao || '').match(/^(.*?)\s*\((\d+(?:[.,]\d+)?)\s+(.+)\)$/)
  const qtd = m ? parseFloat(m[2].replace(',', '.')) : 1
  editando.value = true
  requisitoId.value = atividade.rsa_requisito
  quantidade.value = qtd
  edicao.value = {
    atividade,
    descricaoBase: m ? m[1] : atividade.rsa_descricao,
    unidade: m ? m[3] : '',
    pontosUnidade: qtd > 0 ? Math.round((atividade.rsa_pontos / qtd) * 10000) / 10000 : 0,
  }
  aberto.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { data } = editando.value ? await salvarEdicao() : await salvarNova()
    emit('salvo', data.calculos)
    Notify.create({ type: 'positive', message: data.message, position: 'top' })
    aberto.value = false
  } catch {
    // Erro já exibido pelo interceptor do axios.
  } finally {
    salvando.value = false
  }
}

function salvarNova() {
  const item = selecionado.value
  const obs = observacao.value
    ? `Item nº ${item.item_numero} — ${observacao.value}`
    : `Item nº ${item.item_numero} · ${item.item_pontos_unidade} pt/${item.item_unidade}`
  return rsc.adicionarAtividade(props.rscHashid, {
    rsa_requisito: requisitoId.value,
    rsa_descricao: `${item.item_descricao} (${quantidade.value} ${item.item_unidade})`,
    rsa_pontos: pontos.value,
    rsa_observacoes: obs,
  })
}

function salvarEdicao() {
  const { atividade, descricaoBase, unidade } = edicao.value
  return rsc.atualizarAtividade(atividade.rsa_hashid, {
    rsa_requisito: atividade.rsa_requisito,
    rsa_descricao: unidade ? `${descricaoBase} (${quantidade.value} ${unidade})` : descricaoBase,
    rsa_pontos: pontos.value,
    rsa_observacoes: atividade.rsa_observacoes,
  })
}

defineExpose({ abrirAdicionar, abrirEditar })
</script>
