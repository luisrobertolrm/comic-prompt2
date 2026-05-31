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
}

export interface ProjectDetailOut extends ProjectOut {
  premise: string | null;
  characters: CharacterOut[];
}

export interface CharacterOut {
  id: string;
  name: string;
  role: string;
  age: number | null;
  height: string | null;
  summary: string | null;
  outfit: string | null;
  traits: string[];
  approved: boolean;
  image_url: string | null;
}

export interface CharacterCreate {
  name: string;
  role?: string;
  age?: number;
  height?: string;
  summary?: string;
  outfit?: string;
  traits?: string[];
  image_url?: string;
}

export interface PortraitCandidate {
  id: string;
  url: string;
  notes: string;
}
