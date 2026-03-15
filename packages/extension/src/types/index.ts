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
  provider: 'openai' | 'anthropic' | 'ollama' | 'nrp';
  model: string;
  temperature: number;
  pipeline_duration_ms: number;
}

import type {
  AgentConfig,
  CommunicationLog,
  CrossReferenceAnalysis,
  FundamentalsSnapshot,
  MacroContext,
  NewsItem,
} from './enriched';

export type { AgentConfig, CommunicationLog, CrossReferenceAnalysis, FundamentalsSnapshot, MacroContext, NewsItem };
export type { AgentMessage, Divergence, FinancialMetric } from './enriched';

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
  news_context?: NewsItem[] | null;
  fundamentals_summary?: FundamentalsSnapshot[] | null;
  cross_reference_analysis?: CrossReferenceAnalysis | null;
  macro_context?: MacroContext | null;
  agent_attributions?: Record<string, string[]> | null;
  communication_log?: CommunicationLog | null;
}

export interface UserSettings {
  provider: 'openai' | 'anthropic' | 'ollama' | 'nrp';
  model: string;
  api_key?: string;
  base_url?: string;
  temperature: number;
  pii_redaction: boolean;
  web_lookup: boolean;
  agent_configs?: AgentConfig[];
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
