// Textos e tabelas usados só para exibição. As regras de cálculo ficam no backend.

export const ESCOLARIDADES = [
  { value: 'fund_incompleto', label: 'Ensino Fundamental Incompleto' },
  { value: 'fund_completo', label: 'Ensino Fundamental Completo' },
  { value: 'medio', label: 'Ensino Médio / Técnico' },
  { value: 'graduacao', label: 'Graduação' },
  { value: 'especializacao', label: 'Pós-Graduação (Especialização)' },
  { value: 'mestrado', label: 'Mestrado' },
  { value: 'doutorado', label: 'Doutorado' },
]

export const NIVEL_INDICADO_POR_ESCOLARIDADE = {
  fund_incompleto: 'RSC-I',
  fund_completo: 'RSC-II',
  medio: 'RSC-III',
  graduacao: 'RSC-IV',
  especializacao: 'RSC-V',
  mestrado: 'RSC-VI',
  doutorado: null,
}

export const REQUISITOS = [
  { id: 'I', titulo: 'Participação em Representações', icon: 'groups', color: 'indigo',
    descricao: 'Comissões, grupos de trabalho, conselhos, núcleos e representações formalmente instituídos.' },
  { id: 'II', titulo: 'Projetos Institucionais', icon: 'science', color: 'teal',
    descricao: 'Participação em projetos de pesquisa, extensão, ensino, inovação e assistência técnica.' },
  { id: 'III', titulo: 'Premiações', icon: 'emoji_events', color: 'amber-9',
    descricao: 'Premiações e reconhecimentos públicos por projetos implementados na administração pública.' },
  { id: 'IV', titulo: 'Responsabilidades Técnico-Administrativas', icon: 'engineering', color: 'orange',
    descricao: 'Designação para responsabilidades técnicas ou especializadas (contratos, licitações, tempo de serviço).' },
  { id: 'V', titulo: 'Funções Gratificadas e Cargos de Direção', icon: 'manage_accounts', color: 'purple',
    descricao: 'Exercício de Função Gratificada (FG), Cargo de Direção (CD) ou assessoramento institucional.' },
  { id: 'VI', titulo: 'Produção de Conhecimento', icon: 'menu_book', color: 'red-8',
    descricao: 'Artigos, livros, patentes, certificações, capacitações, orientações e produções técnicas.' },
]

export const rotuloEscolaridade = (valor) =>
  ESCOLARIDADES.find((e) => e.value === valor)?.label || valor

export const formatarPontos = (valor) => Number(valor || 0).toLocaleString('pt-BR')
