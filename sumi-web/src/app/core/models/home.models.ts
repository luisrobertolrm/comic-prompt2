export interface ProjectOut {
  id: string;
  title: string;
  subtitle: string;
  genre: string;
  tone: string;
  status: string;
  pages: number;
  style: string;
  cover_accent: string;
  cover_tone: string;
  updated_at: string;
}

export interface ProjectCreate {
  premise: string;
  genre: string;
  tone: string;
  pages: number;
  language: string;
  style: string;
  narrator_voice_id?: string | null;
}

export interface ProjectDetailOut extends ProjectOut {
  premise: string | null;
  synopsis: string | null;
  narrator_voice_id: string | null;
  characters: CharacterOut[];
}

export interface ProjectUpdate {
  premise?: string;
  synopsis?: string;
  genre?: string;
  tone?: string;
  pages?: number;
  style?: string;
  narrator_voice_id?: string | null;
}

export interface CharacterOut {
  id: string;
  name: string;
  role: string;
  gender: string | null;
  age: number | null;
  height: string | null;
  summary: string | null;
  outfit: string | null;
  traits: string[];
  style: string;
  approved: boolean;
  image_url: string | null;
  narrator_voice_id: string | null;
  project_count: number;
}

export interface CharacterCreate {
  name: string;
  role?: string;
  gender?: string;
  age?: number;
  height?: string;
  summary?: string;
  outfit?: string;
  traits?: string[];
  style?: string;
  image_url?: string;
  narrator_voice_id?: string | null;
}

export interface CharacterUpdate {
  name?: string;
  role?: string;
  gender?: string | null;
  age?: number | null;
  height?: string | null;
  summary?: string | null;
  outfit?: string | null;
  traits?: string[];
  image_url?: string;
  narrator_voice_id?: string | null;
}

export interface PortraitCandidate {
  id: string;
  url: string;
  notes: string;
}

export interface PortraitJob {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  portraits: PortraitCandidate[];
  detail: string;
}
