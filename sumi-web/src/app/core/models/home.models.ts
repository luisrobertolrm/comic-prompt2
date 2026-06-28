export interface ProjectOut {
  id: string;
  title: string;
  subtitle: string;
  genre: string;
  tone: string;
  status: string;
  pages: number;
  style: string;
  color_mode: string;
  cover_accent: string;
  cover_tone: string;
  video_url: string | null;
  synopsis_temperature: number;
  panels_temperature: number;
  updated_at: string;
}

export interface ProjectCreate {
  title: string;
  premise: string;
  genre: string;
  tone: string;
  pages: number;
  language: string;
  style: string;
  color_mode: string;
  narrator_voice_id?: string | null;
}

export interface ProjectDetailOut extends ProjectOut {
  premise: string | null;
  synopsis: string | null;
  narrator_voice_id: string | null;
  characters: CharacterOut[];
  scenarios: ScenarioOut[];
}

export interface ProjectUpdate {
  title?: string;
  premise?: string;
  synopsis?: string;
  genre?: string;
  tone?: string;
  pages?: number;
  style?: string;
  color_mode?: string;
  narrator_voice_id?: string | null;
  synopsis_temperature?: number;
  panels_temperature?: number;
}

export interface SeriesOut {
  id: string;
  name: string;
  description: string | null;
  project_ids: string[];
  updated_at: string;
}

export interface SeriesCreate {
  name: string;
  description?: string | null;
}

export interface SeriesUpdate {
  name?: string;
  description?: string | null;
}

export interface CharacterOut {
  id: string;
  name: string;
  role: string;
  gender: string | null;
  body_type: string | null;
  skin_tone: string | null;
  ethnicity: string | null;
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
  body_type?: string;
  skin_tone?: string;
  ethnicity?: string;
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
  body_type?: string | null;
  skin_tone?: string | null;
  ethnicity?: string | null;
  age?: number | null;
  height?: string | null;
  summary?: string | null;
  outfit?: string | null;
  traits?: string[];
  image_url?: string;
  narrator_voice_id?: string | null;
}

export interface AttrOption {
  id: string;
  label: string;
}

export interface AttrGroup {
  id: string;
  label: string;
  multi: boolean;
  options: AttrOption[];
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

export interface ScenarioOut {
  id: string;
  name: string;
  kind: string;
  summary: string | null;
  location_type: string | null;
  time_of_day: string | null;
  weather: string | null;
  atmosphere: string | null;
  details: string | null;
  style: string;
  approved: boolean;
  image_url: string | null;
  project_count: number;
}

export interface ScenarioCreate {
  name: string;
  kind?: string;
  summary?: string;
  location_type?: string;
  time_of_day?: string;
  weather?: string;
  atmosphere?: string;
  details?: string;
  style?: string;
  image_url?: string;
}

export interface ScenarioUpdate {
  name?: string;
  kind?: string;
  summary?: string | null;
  location_type?: string | null;
  time_of_day?: string | null;
  weather?: string | null;
  atmosphere?: string | null;
  details?: string | null;
  image_url?: string;
}

export interface SceneCandidate {
  id: string;
  url: string;
  notes: string;
}

export interface SceneJob {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  scenes: SceneCandidate[];
  detail: string;
}
