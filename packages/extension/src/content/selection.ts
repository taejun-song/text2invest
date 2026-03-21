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
let tooltipHost: HTMLElement | null = null;
let contextValid = true;

function safeSendMessage(message: unknown): void {
  if (!contextValid) return;
  try {
    chrome.runtime.sendMessage(message);
  } catch {
    contextValid = false;
    removeTooltip();
    document.removeEventListener('selectionchange', handleSelectionChange);
  }
}

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

const TOOLTIP_STYLES = `
  :host {
    position: fixed;
    z-index: 2147483647;
  }
  .t2i-tooltip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: #1a1a2e;
    border: 1px solid #3a3a5c;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    animation: t2i-fadein 0.15s ease-out;
  }
  .t2i-tooltip button {
    all: unset;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    border-radius: 6px;
    white-space: nowrap;
    transition: opacity 0.15s;
  }
  .t2i-tooltip button:hover { opacity: 0.85; }
  .t2i-tooltip button svg {
    width: 14px;
    height: 14px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
  @keyframes t2i-fadein {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

function removeTooltip(): void {
  if (tooltipHost) {
    tooltipHost.remove();
    tooltipHost = null;
  }
}

function showTooltip(state: SelectionState): void {
  removeTooltip();
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return;

  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  if (rect.width === 0 && rect.height === 0) return;

  tooltipHost = document.createElement('div');
  tooltipHost.id = 't2i-tooltip-host';
  const shadow = tooltipHost.attachShadow({ mode: 'closed' });

  const style = document.createElement('style');
  style.textContent = TOOLTIP_STYLES;

  const container = document.createElement('div');
  container.className = 't2i-tooltip';

  const btn = document.createElement('button');
  btn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>Generate Idea`;
  btn.addEventListener('mousedown', (e) => {
    e.preventDefault();
    e.stopPropagation();
    safeSendMessage({
      type: 'GENERATE_FROM_CONTENT',
      payload: { text: state.text, url: state.url, title: state.title },
    });
    removeTooltip();
  });

  container.appendChild(btn);
  shadow.appendChild(style);
  shadow.appendChild(container);

  const left = Math.min(rect.right, window.innerWidth - 160);
  const top = rect.bottom + 6;
  tooltipHost.style.left = `${Math.max(0, left)}px`;
  tooltipHost.style.top = `${top}px`;

  if (top + 40 > window.innerHeight) {
    tooltipHost.style.top = `${rect.top - 40}px`;
  }

  document.documentElement.appendChild(tooltipHost);
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
      showTooltip(state);
      safeSendMessage({
        type: 'SELECTION_CHANGED',
        payload: {
          text: state.text,
          url: state.url,
          title: state.title,
          truncated: state.truncated,
        },
      });
    } else {
      removeTooltip();
      safeSendMessage({ type: 'SELECTION_CLEARED' });
    }
  }, DEBOUNCE_MS);
}

document.addEventListener('selectionchange', handleSelectionChange);

document.addEventListener('mousedown', (e) => {
  if (tooltipHost && !tooltipHost.contains(e.target as Node)) {
    removeTooltip();
  }
});

try {
  chrome.runtime.onMessage.addListener(
    (message: { type: string }, _sender, sendResponse: (response: unknown) => void) => {
      try {
        if (message.type === 'GET_SELECTION') {
          const selection = window.getSelection();
          const text = selection?.toString() || '';
          const state = validateSelection(text);
          sendResponse(state);
        }
      } catch {
        contextValid = false;
      }
      return true;
    }
  );
} catch {
  contextValid = false;
}

window.addEventListener('beforeunload', () => {
  if (lastSelection?.valid) {
    safeSendMessage({ type: 'NAVIGATION_AWAY' });
  }
});
