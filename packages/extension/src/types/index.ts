export interface Source {
  url: string;
  title: string;
}

export type SearchDepth = 'focused' | 'standard' | 'expanded';

export type Signal = 'BUY' | 'SELL' | 'HOLD';

export type RelationshipType = 'competitor' | 'supplier' | 'customer' | 'sector_peer' | 'parent_subsidiary';

export interface Recommendation {
  signal: Signal;
  certainty: number;
  rationale: string;
  factors: string[];
}

export interface Ticker {
  symbol: string;
  company_name: string;
  confidence: number;
  recommendation?: Recommendation | null;
}

export interface RelatedTicker {
  symbol: string;
  company_name: string;
  relationship: RelationshipType;
  primary_symbol: string;
  depth: number;
  recommendation?: Recommendation | null;
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

export interface QuantitativeEntry {
  ticker: string;
  company_name: string;
  fundamentals: {
    pe_ratio?: number | null;
    market_cap?: string | null;
    revenue?: string | null;
    profit_margin?: number | null;
    dividend_yield?: number | null;
    eps?: number | null;
  };
  technicals?: {
    current_price?: number | null;
    ma_50?: number | null;
    ma_200?: number | null;
    rsi_14?: number | null;
    price_change_1w?: number | null;
    price_change_1m?: number | null;
    price_change_3m?: number | null;
  } | null;
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
  confidence_score?: number | null;
  confidence_explanation?: string | null;
  quantitative_data?: QuantitativeEntry[];
  limitations: string[];
  provider_meta: ProviderMeta;
  news_context?: NewsItem[] | null;
  fundamentals_summary?: FundamentalsSnapshot[] | null;
  cross_reference_analysis?: CrossReferenceAnalysis | null;
  macro_context?: MacroContext | null;
  agent_attributions?: Record<string, string[]> | null;
  communication_log?: CommunicationLog | null;
  thinking_output?: Record<string, AgentThinking> | null;
  related_tickers?: RelatedTicker[];
  search_depth?: SearchDepth | null;
  disclaimer?: string;
}

export interface AgentThinking {
  agent_id: string;
  phase: 'sequential' | 'parallel';
  content: string;
}

export interface ThinkingChunk {
  agent_id: string;
  phase: 'sequential' | 'parallel';
  content: string;
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
  thinking_mode: boolean;
  output_language?: string;
  search_depth?: SearchDepth;
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
  user_tickers?: UserTicker[];
}

export interface AgentResult {
  agent_id: string;
  summary: Record<string, unknown>;
}

export interface GenerationState {
  status: 'idle' | 'generating' | 'completed' | 'failed';
  request_id?: string;
  started_at?: string;
  current_stage?: string;
  completed_stages?: string[];
  enrichment_agents?: string[];
  thinking_chunks?: ThinkingChunk[];
  agent_results?: AgentResult[];
  error?: string;
  report?: IdeaReport;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface RateLimitError {
  error: 'rate_limited';
  message: string;
  retry_after_seconds?: number;
}

export interface UserTicker {
  symbol: string;
  company_name?: string;
}
