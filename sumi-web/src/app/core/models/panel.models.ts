export interface Bubble {
  text: string;
  kind: 'say' | 'thought' | 'shout';
  side: 'left' | 'right';
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
}
