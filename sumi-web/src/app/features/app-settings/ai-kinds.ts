import type { AiType } from '../../core/services/ai-config.api';

export interface AiKind {
  kind: string;
  label: string;
  defaultUrl: string;
}

export interface AiTab {
  type: AiType;
  label: string;
  /** Usado em "Nenhuma IA de <noun> ativa". */
  noun: string;
  hint: string;
  kinds: AiKind[];
  urlHint?: string;
}

const OPENAI_URL = 'https://api.openai.com/v1';
const MINIMAX_URL = 'https://api.minimax.io';

export const AI_TABS: AiTab[] = [
  {
    type: 'text',
    label: 'Texto',
    noun: 'texto',
    hint: 'Sinopse, roteiro e metadados do YouTube.',
    kinds: [
      { kind: 'openai', label: 'OpenAI-compatível', defaultUrl: OPENAI_URL },
      { kind: 'anthropic', label: 'Anthropic', defaultUrl: 'https://api.anthropic.com' },
    ],
    urlHint: 'ByteDance: https://ark.ap-southeast.bytepluses.com/api/v3 · MiniMax: https://api.minimax.io/v1',
  },
  {
    type: 'image',
    label: 'Imagem',
    noun: 'imagem',
    hint: 'Retratos, cenários e painéis. O teste gera 1 imagem e consome créditos.',
    kinds: [
      { kind: 'openai', label: 'OpenAI', defaultUrl: OPENAI_URL },
      { kind: 'seedream', label: 'Seedream (ByteDance)', defaultUrl: 'https://ark.ap-southeast.bytepluses.com/api/v3' },
      { kind: 'minimax', label: 'MiniMax', defaultUrl: MINIMAX_URL },
    ],
  },
  {
    type: 'transcription',
    label: 'Transcrição',
    noun: 'transcrição',
    hint: 'Ditado por voz nos campos de texto (Ctrl+Shift+Espaço).',
    kinds: [{ kind: 'openai', label: 'OpenAI-compatível', defaultUrl: OPENAI_URL }],
  },
  {
    type: 'voice',
    label: 'Voz',
    noun: 'voz',
    hint: 'Narração e teste de voz.',
    kinds: [{ kind: 'minimax', label: 'MiniMax', defaultUrl: MINIMAX_URL }],
  },
  {
    type: 'video',
    label: 'Vídeo',
    noun: 'vídeo',
    hint: 'O teste só valida a conexão; não gera vídeo.',
    kinds: [{ kind: 'minimax', label: 'MiniMax', defaultUrl: MINIMAX_URL }],
  },
];

export function kindLabel(tab: AiTab, kind: string): string {
  return tab.kinds.find(k => k.kind === kind)?.label ?? kind;
}
