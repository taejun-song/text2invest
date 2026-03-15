export interface NewsItem {
  headline: string;
  source: string;
  url: string;
  published_date: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  relevance_score: number;
  summary: string;
  data_source: 'web_search' | 'llm_knowledge';
}

export interface FinancialMetric {
  name: string;
  value: string;
  period?: string;
}

export interface FundamentalsSnapshot {
  ticker: string;
  company_name: string;
  metrics: FinancialMetric[];
  data_source: 'web_search' | 'llm_knowledge';
  retrieved_at: string;
}

export interface Divergence {
  topic: string;
  finding_a: string;
  source_a: string;
  finding_b: string;
  source_b: string;
  explanation: string;
}

export interface CrossReferenceAnalysis {
  convergences: string[];
  divergences: Divergence[];
  deduplicated_risks: string[];
}

export interface MacroContext {
  sector: string;
  sector_trends: string[];
  economic_indicators: string[];
  headwinds: string[];
  tailwinds: string[];
  data_source: 'web_search' | 'llm_knowledge';
}

export interface AgentMessage {
  id: string;
  sender: string;
  recipient: string;
  message_type: 'finding' | 'query' | 'challenge' | 'response';
  content: Record<string, unknown>;
  timestamp: string;
  round_number: number;
}

export interface CommunicationLog {
  id: string;
  messages: AgentMessage[];
  total_rounds: number;
  duration_ms: number;
}

export interface AgentConfig {
  agent_id: 'news_agent' | 'fundamentals_agent' | 'risk_agent' | 'macro_agent';
  enabled: boolean;
  use_external_data: boolean;
}
