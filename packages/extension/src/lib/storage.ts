import type { Evaluation, GenerationState, IdeaReport, UserSettings } from '../types';

const KEYS = {
  SETTINGS: 'settings',
  REPORTS: 'reports',
  EVALUATIONS: 'evaluations',
  GENERATION_STATE: 'generation_state',
} as const;

export async function getSettings(): Promise<UserSettings | null> {
  const result = await chrome.storage.local.get(KEYS.SETTINGS);
  return result[KEYS.SETTINGS] ?? null;
}

export async function saveSettings(settings: UserSettings): Promise<void> {
  await chrome.storage.local.set({ [KEYS.SETTINGS]: settings });
}

export async function getReports(): Promise<IdeaReport[]> {
  const result = await chrome.storage.local.get(KEYS.REPORTS);
  return result[KEYS.REPORTS] ?? [];
}

export async function saveReport(report: IdeaReport): Promise<void> {
  const reports = await getReports();
  reports.unshift(report);
  await chrome.storage.local.set({ [KEYS.REPORTS]: reports });
}

export async function getReportById(id: string): Promise<IdeaReport | null> {
  const reports = await getReports();
  return reports.find((r) => r.id === id) ?? null;
}

export async function getEvaluations(): Promise<Evaluation[]> {
  const result = await chrome.storage.local.get(KEYS.EVALUATIONS);
  return result[KEYS.EVALUATIONS] ?? [];
}

export async function saveEvaluation(evaluation: Evaluation): Promise<void> {
  const evaluations = await getEvaluations();
  const existing = evaluations.findIndex((e) => e.idea_id === evaluation.idea_id);
  if (existing >= 0) {
    evaluations[existing] = evaluation;
  } else {
    evaluations.push(evaluation);
  }
  await chrome.storage.local.set({ [KEYS.EVALUATIONS]: evaluations });
}

export async function getEvaluationByIdeaId(ideaId: string): Promise<Evaluation | null> {
  const evaluations = await getEvaluations();
  return evaluations.find((e) => e.idea_id === ideaId) ?? null;
}

export async function getGenerationState(): Promise<GenerationState> {
  const result = await chrome.storage.local.get(KEYS.GENERATION_STATE);
  return result[KEYS.GENERATION_STATE] ?? { status: 'idle' };
}

export async function setGenerationState(state: GenerationState): Promise<void> {
  await chrome.storage.local.set({ [KEYS.GENERATION_STATE]: state });
}

export async function searchReports(query: string): Promise<IdeaReport[]> {
  const reports = await getReports();
  const lowerQuery = query.toLowerCase();
  return reports.filter((report) => {
    const tickerMatch = report.tickers.some(
      (t) =>
        t.symbol.toLowerCase().includes(lowerQuery) ||
        t.company_name.toLowerCase().includes(lowerQuery)
    );
    const domainMatch = new URL(report.source.url).hostname.toLowerCase().includes(lowerQuery);
    const dateMatch = report.created_at.includes(query);
    return tickerMatch || domainMatch || dateMatch;
  });
}
