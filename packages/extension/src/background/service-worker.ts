import { cancelGeneration, generateIdea, generateIdeaStream } from '../lib/api';
import {
  getGenerationState,
  getSettings,
  saveReport,
  setGenerationState,
} from '../lib/storage';
import type { AgentResult, GenerationState, IdeaRequest, ThinkingChunk } from '../types';

interface Message {
  type: string;
  payload?: unknown;
}

interface GenerateMessage extends Message {
  type: 'GENERATE';
  payload: {
    selection_text: string;
    url: string;
    title: string;
  };
}

interface CancelMessage extends Message {
  type: 'CANCEL';
}

interface GetStateMessage extends Message {
  type: 'GET_STATE';
}

interface SelectionChangedMessage extends Message {
  type: 'SELECTION_CHANGED';
  payload: {
    text: string;
    url: string;
    title: string;
    truncated: boolean;
  };
}

interface SelectionClearedMessage extends Message {
  type: 'SELECTION_CLEARED';
}

interface NavigationAwayMessage extends Message {
  type: 'NAVIGATION_AWAY';
}

interface GenerateFromContentMessage extends Message {
  type: 'GENERATE_FROM_CONTENT';
  payload: {
    text: string;
    url: string;
    title: string;
  };
}

type ExtensionMessage =
  | GenerateMessage
  | CancelMessage
  | GetStateMessage
  | SelectionChangedMessage
  | SelectionClearedMessage
  | NavigationAwayMessage
  | GenerateFromContentMessage;

chrome.runtime.onMessage.addListener(
  (message: ExtensionMessage, sender, sendResponse: (response: unknown) => void) => {
    handleMessage(message, sender).then(sendResponse);
    return true;
  }
);

async function handleMessage(
  message: ExtensionMessage,
  sender: chrome.runtime.MessageSender
): Promise<unknown> {
  switch (message.type) {
    case 'GENERATE':
      return handleGenerate(message.payload);
    case 'CANCEL':
      return handleCancel();
    case 'GET_STATE':
      return getGenerationState();
    case 'SELECTION_CHANGED':
      return handleSelectionChanged(message.payload);
    case 'SELECTION_CLEARED':
      return handleSelectionCleared();
    case 'GENERATE_FROM_CONTENT':
      return handleGenerateFromContent(message.payload, sender);
    case 'NAVIGATION_AWAY':
      return handleNavigationAway();
    default:
      return { error: 'Unknown message type' };
  }
}

async function handleGenerate(payload: GenerateMessage['payload']): Promise<GenerationState> {
  const settings = await getSettings();
  if (!settings) {
    return {
      status: 'failed',
      error: 'No provider configured. Please configure settings first.',
    };
  }

  const requestId = crypto.randomUUID();
  const completedStages: string[] = [];
  let enrichmentAgents: string[] = [];
  const thinkingChunks: ThinkingChunk[] = [];
  const agentResults: AgentResult[] = [];

  await setGenerationState({
    status: 'generating',
    request_id: requestId,
    started_at: new Date().toISOString(),
    current_stage: 'starting',
    completed_stages: [],
    enrichment_agents: [],
    thinking_chunks: [],
    agent_results: [],
  });

  try {
    const request: IdeaRequest = {
      selection_text: payload.selection_text,
      url: payload.url,
      title: payload.title,
      user_settings: settings,
    };

    let report;
    try {
      report = await generateIdeaStream(
        request,
        async (stage: string) => {
          if (stage.startsWith('enrichment:') && !stage.startsWith('enrichment:risk') && !stage.startsWith('enrichment:synthesis')) {
            enrichmentAgents = stage.slice('enrichment:'.length).split(',');
            completedStages.push('enrichment');
          } else if (stage.startsWith('agent_done:')) {
            const agentId = stage.slice('agent_done:'.length);
            completedStages.push(`agent:${agentId}`);
          } else if (stage.startsWith('enrichment:')) {
            completedStages.push(stage);
          } else {
            completedStages.push(stage);
          }
          await setGenerationState({
            status: 'generating',
            request_id: requestId,
            current_stage: stage,
            completed_stages: [...completedStages],
            enrichment_agents: [...enrichmentAgents],
            thinking_chunks: [...thinkingChunks],
            agent_results: [...agentResults],
          });
        },
        settings.thinking_mode
          ? (agentId: string, phase: string, content: string) => {
              const existing = thinkingChunks.find((c) => c.agent_id === agentId);
              if (existing) {
                existing.content += content;
              } else {
                thinkingChunks.push({ agent_id: agentId, phase: phase as 'sequential' | 'parallel', content });
              }
              setGenerationState({
                status: 'generating',
                request_id: requestId,
                current_stage: 'thinking',
                completed_stages: [...completedStages],
                enrichment_agents: [...enrichmentAgents],
                thinking_chunks: [...thinkingChunks],
                agent_results: [...agentResults],
              });
            }
          : undefined,
        (agentId: string, summary: Record<string, unknown>) => {
          agentResults.push({ agent_id: agentId, summary });
          setGenerationState({
            status: 'generating',
            request_id: requestId,
            current_stage: `result:${agentId}`,
            completed_stages: [...completedStages],
            enrichment_agents: [...enrichmentAgents],
            thinking_chunks: [...thinkingChunks],
            agent_results: [...agentResults],
          });
        },
      );
    } catch {
      report = await generateIdea(request);
    }

    if (thinkingChunks.length > 0) {
      const output: Record<string, import('../types').AgentThinking> = {};
      for (const chunk of thinkingChunks) {
        output[chunk.agent_id] = { agent_id: chunk.agent_id, phase: chunk.phase, content: chunk.content };
      }
      report.thinking_output = output;
    }
    await saveReport(report);
    const state: GenerationState = {
      status: 'completed',
      request_id: requestId,
      report,
    };
    await setGenerationState(state);
    return state;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    const state: GenerationState = {
      status: 'failed',
      request_id: requestId,
      error: errorMessage,
    };
    await setGenerationState(state);
    return state;
  }
}

async function handleCancel(): Promise<{ cancelled: boolean }> {
  const state = await getGenerationState();
  if (state.status === 'generating' && state.request_id) {
    try {
      await cancelGeneration(state.request_id);
      await setGenerationState({ status: 'idle' });
      return { cancelled: true };
    } catch {
      return { cancelled: false };
    }
  }
  return { cancelled: false };
}

async function handleGenerateFromContent(
  payload: GenerateFromContentMessage['payload'],
  sender: chrome.runtime.MessageSender
): Promise<GenerationState> {
  const tabId = sender.tab?.id;
  if (tabId !== undefined) {
    try { await chrome.sidePanel.open({ tabId }); } catch {}
  }
  return handleGenerate({
    selection_text: payload.text,
    url: payload.url,
    title: payload.title,
  });
}

let currentSelection: SelectionChangedMessage['payload'] | null = null;

function handleSelectionChanged(payload: SelectionChangedMessage['payload']): { stored: boolean } {
  currentSelection = payload;
  return { stored: true };
}

function handleSelectionCleared(): { cleared: boolean } {
  currentSelection = null;
  return { cleared: true };
}

async function handleNavigationAway(): Promise<{ cancelled: boolean }> {
  const state = await getGenerationState();
  if (state.status === 'generating' && state.request_id) {
    try {
      await cancelGeneration(state.request_id);
      await setGenerationState({ status: 'idle' });
      return { cancelled: true };
    } catch {
      return { cancelled: false };
    }
  }
  return { cancelled: false };
}

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false });
