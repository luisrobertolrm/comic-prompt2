export type BubbleKind = 'say' | 'thought' | 'shout' | 'whisper' | 'narration';
export type BubbleTail = 'none' | 'left' | 'right';

export interface Bubble {
  text: string;
  kind: BubbleKind;
  side: 'left' | 'right';
  tail: BubbleTail;
  x: number;
  y: number;
}

export interface PanelOut {
  id: string;
  project_id: string;
  index_order: number;
  label: string;
  aspect: string;
  tone: string;
  character_name: string | null;
  caption: string;
  framing: string;
  prompt: string;
  status: string;
  bubbles: Bubble[];
  image_url: string | null;
  synopsis_start: number | null;
  synopsis_end: number | null;
}

export interface PanelPatch {
  label?: string;
  aspect?: string;
  tone?: string;
  character_name?: string | null;
  caption?: string;
  framing?: string;
  prompt?: string;
  status?: string;
  bubbles?: Bubble[];
  synopsis_start?: number | null;
  synopsis_end?: number | null;
}
