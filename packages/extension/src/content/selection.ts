const MIN_SELECTION_LENGTH = 20;
const MAX_SELECTION_LENGTH = 8000;
const DEBOUNCE_MS = 600;

interface SelectionState {
  text: string;
  url: string;
  title: string;
  truncated: boolean;
  valid: boolean;
  error?: string;
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null;
let lastSelection: SelectionState | null = null;

const PII_PATTERNS = {
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  phone: /\b(?:\+?1[-.\s]?)?(?:\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b/g,
  ssn: /\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b/g,
};

function redactPII(text: string): string {
  let redacted = text;
  redacted = redacted.replace(PII_PATTERNS.email, '[EMAIL REDACTED]');
  redacted = redacted.replace(PII_PATTERNS.phone, '[PHONE REDACTED]');
  redacted = redacted.replace(PII_PATTERNS.ssn, '[SSN REDACTED]');
  return redacted;
}

function validateSelection(text: string): SelectionState {
  const url = window.location.href;
  const title = document.title;

  if (!text || text.trim().length === 0) {
    return { text: '', url, title, truncated: false, valid: false };
  }

  const trimmedText = text.trim();

  if (trimmedText.length < MIN_SELECTION_LENGTH) {
    return {
      text: trimmedText,
      url,
      title,
      truncated: false,
      valid: false,
      error: `Selection must be at least ${MIN_SELECTION_LENGTH} characters`,
    };
  }

  let finalText = trimmedText;
  let truncated = false;

  if (trimmedText.length > MAX_SELECTION_LENGTH) {
    finalText = trimmedText.substring(0, MAX_SELECTION_LENGTH);
    truncated = true;
  }

  return {
    text: redactPII(finalText),
    url,
    title,
    truncated,
    valid: true,
  };
}

function handleSelectionChange(): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  debounceTimer = setTimeout(() => {
    const selection = window.getSelection();
    const text = selection?.toString() || '';
    const state = validateSelection(text);
    lastSelection = state;

    if (state.valid) {
      chrome.runtime.sendMessage({
        type: 'SELECTION_CHANGED',
        payload: {
          text: state.text,
          url: state.url,
          title: state.title,
          truncated: state.truncated,
        },
      });
    } else {
      chrome.runtime.sendMessage({
        type: 'SELECTION_CLEARED',
      });
    }
  }, DEBOUNCE_MS);
}

document.addEventListener('selectionchange', handleSelectionChange);

chrome.runtime.onMessage.addListener(
  (message: { type: string }, _sender, sendResponse: (response: unknown) => void) => {
    if (message.type === 'GET_SELECTION') {
      const selection = window.getSelection();
      const text = selection?.toString() || '';
      const state = validateSelection(text);
      sendResponse(state);
    }
    return true;
  }
);

window.addEventListener('beforeunload', () => {
  if (lastSelection?.valid) {
    chrome.runtime.sendMessage({ type: 'NAVIGATION_AWAY' });
  }
});
