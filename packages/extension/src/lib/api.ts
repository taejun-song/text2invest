import type {
  ChatMessage,
  ErrorResponse,
  Evaluation,
  IdeaReport,
  IdeaRequest,
  RateLimitError,
  UserSettings,
} from '../types';

const BASE_URL = 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly response: ErrorResponse | RateLimitError
  ) {
    super(response.message);
    this.name = 'ApiError';
  }

  isRateLimited(): this is { response: RateLimitError } {
    return this.status === 429;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = (await response.json()) as ErrorResponse | RateLimitError;
    throw new ApiError(response.status, error);
  }
  return response.json() as Promise<T>;
}

export async function generateIdea(request: IdeaRequest): Promise<IdeaReport> {
  const response = await fetch(`${BASE_URL}/api/v1/ideas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<IdeaReport>(response);
}

export async function generateIdeaStream(
  request: IdeaRequest,
  onStage: (stage: string) => void,
  onThinking?: (agentId: string, phase: string, content: string) => void,
  onAgentResult?: (agentId: string, summary: Record<string, unknown>) => void
): Promise<IdeaReport> {
  const response = await fetch(`${BASE_URL}/api/v1/ideas/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = (await response.json()) as ErrorResponse | RateLimitError;
    throw new ApiError(response.status, error);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let report: IdeaReport | null = null;
  let streamError: string | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split('\n\n');
    buffer = parts.pop()!;

    for (const part of parts) {
      const lines = part.split('\n');
      let event = '';
      let data = '';
      for (const line of lines) {
        if (line.startsWith('event: ')) event = line.slice(7);
        else if (line.startsWith('data: ')) data = line.slice(6);
      }
      if (event === 'stage') {
        const parsed = JSON.parse(data) as { stage: string };
        onStage(parsed.stage);
      } else if (event === 'thinking' && onThinking) {
        const parsed = JSON.parse(data) as { agent_id: string; phase: string; content: string };
        onThinking(parsed.agent_id, parsed.phase, parsed.content);
      } else if (event === 'agent_result' && onAgentResult) {
        const parsed = JSON.parse(data) as { agent_id: string; summary: Record<string, unknown> };
        onAgentResult(parsed.agent_id, parsed.summary);
      } else if (event === 'complete') {
        report = JSON.parse(data) as IdeaReport;
      } else if (event === 'error') {
        const parsed = JSON.parse(data) as { error: string };
        streamError = parsed.error;
      }
    }
  }

  if (streamError) throw new Error(streamError);
  if (!report) throw new Error('Stream ended without a report');
  return report;
}

export async function cancelGeneration(ideaId: string): Promise<{ cancelled: boolean }> {
  const response = await fetch(`${BASE_URL}/api/v1/ideas/${ideaId}/cancel`, {
    method: 'POST',
  });
  return handleResponse<{ cancelled: boolean }>(response);
}

export async function submitEvaluation(
  ideaId: string,
  rating: 'useful' | 'not_useful',
  notes?: string
): Promise<Evaluation> {
  const response = await fetch(`${BASE_URL}/api/v1/evaluation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idea_id: ideaId, rating, notes }),
  });
  return handleResponse<Evaluation>(response);
}

export async function chatWithReport(
  reportContext: Record<string, unknown>,
  messages: Array<{ role: string; content: string }>,
  settings: UserSettings
): Promise<ChatMessage> {
  const response = await fetch(`${BASE_URL}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ report_context: reportContext, messages, user_settings: settings }),
  });
  return handleResponse<ChatMessage>(response);
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${BASE_URL}/health`);
  return handleResponse<{ status: string; version: string }>(response);
}

export interface TickerSearchResult {
  symbol: string;
  name: string;
  exchange: string;
}

export async function searchTickers(query: string, marketHint?: string): Promise<TickerSearchResult[]> {
  const response = await fetch(`${BASE_URL}/api/v1/tickers/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, market_hint: marketHint }),
  });
  return handleResponse<TickerSearchResult[]>(response);
}
