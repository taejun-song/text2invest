export interface Source {
  url: string;
  title: string;
}

export interface Ticker {
  symbol: string;
  company_name: string;
  confidence: number;
}

export interface RationaleQuote {
  quote: string;
  start_offset: number;
  end_offset: number;
}

export interface ProviderMeta {
  provider: 'openai' | 'anthropic' | 'ollama';
  model: string;
  temperature: number;
  pipeline_duration_ms: number;
}

export interface IdeaReport {
  id: string;
  created_at: string;
  source: Source;
  selection_text: string;
  tickers: Ticker[];
  thesis: string;
  executive_summary: string[];
  rationale_quotes: RationaleQuote[];
  catalysts: string[];
  risks: string[];
  counter_thesis: string;
  horizon: 'short' | 'medium' | 'long';
  confidence_score: number;
  confidence_explanation: string;
  limitations: string[];
  provider_meta: ProviderMeta;
}

export interface UserSettings {
  provider: 'openai' | 'anthropic' | 'ollama';
  model: string;
  api_key?: string;
  base_url?: string;
  temperature: number;
  pii_redaction: boolean;
  web_lookup: boolean;
}

export interface Evaluation {
  idea_id: string;
  rating: 'useful' | 'not_useful';
  notes?: string;
  created_at: string;
}

export interface IdeaRequest {
  selection_text: string;
  url: string;
  title: string;
  user_settings: UserSettings;
}

export interface GenerationState {
  status: 'idle' | 'generating' | 'completed' | 'failed';
  request_id?: string;
  started_at?: string;
  current_stage?: string;
  error?: string;
  report?: IdeaReport;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface RateLimitError {
  error: 'rate_limited';
  message: string;
  retry_after_seconds?: number;
}
