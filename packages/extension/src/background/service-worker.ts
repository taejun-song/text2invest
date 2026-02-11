import { cancelGeneration, generateIdea } from '../lib/api';
import {
  getGenerationState,
  getSettings,
  saveReport,
  setGenerationState,
} from '../lib/storage';
import type { GenerationState, IdeaRequest } from '../types';

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

type ExtensionMessage =
  | GenerateMessage
  | CancelMessage
  | GetStateMessage
  | SelectionChangedMessage
  | SelectionClearedMessage
  | NavigationAwayMessage;

chrome.runtime.onMessage.addListener(
  (message: ExtensionMessage, _sender, sendResponse: (response: unknown) => void) => {
    handleMessage(message).then(sendResponse);
    return true;
  }
);

async function handleMessage(message: ExtensionMessage): Promise<unknown> {
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
  await setGenerationState({
    status: 'generating',
    request_id: requestId,
    started_at: new Date().toISOString(),
    current_stage: 'extraction',
  });

  try {
    const request: IdeaRequest = {
      selection_text: payload.selection_text,
      url: payload.url,
      title: payload.title,
      user_settings: settings,
    };

    const report = await generateIdea(request);
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
