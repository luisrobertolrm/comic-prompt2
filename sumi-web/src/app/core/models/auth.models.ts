export interface UserOut {
  id: string;
  name: string;
  email: string | null;
  plan: string;
  group: string;
  approved: boolean;
}

export interface RegisterResponse {
  detail: string;
}

export interface PendingUserOut {
  id: string;
  name: string;
  email: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember: boolean;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  confirm: string;
  terms_accepted: boolean;
}
