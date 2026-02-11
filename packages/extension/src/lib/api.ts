import type {
  ErrorResponse,
  Evaluation,
  IdeaReport,
  IdeaRequest,
  RateLimitError,
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

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${BASE_URL}/health`);
  return handleResponse<{ status: string; version: string }>(response);
}
