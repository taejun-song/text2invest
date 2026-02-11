import type { GenerationState, IdeaReport } from '../types';

const STAGE_LABELS: Record<string, string> = {
  extraction: 'Extracting text...',
  entity: 'Identifying entities...',
  ticker: 'Mapping tickers...',
  thesis: 'Generating thesis...',
  critique: 'Analyzing risks...',
  confidence: 'Calibrating confidence...',
  formatting: 'Formatting report...',
};

interface SelectionResponse {
  text: string;
  url: string;
  title: string;
  truncated: boolean;
  valid: boolean;
  error?: string;
}

class PopupController {
  private statusEl: HTMLElement;
  private selectionPreviewEl: HTMLElement;
  private loadingEl: HTMLElement;
  private loadingTextEl: HTMLElement;
  private resultSummaryEl: HTMLElement;
  private resultTickersEl: HTMLElement;
  private resultConfidenceEl: HTMLElement;
  private generateBtn: HTMLButtonElement;
  private cancelBtn: HTMLButtonElement;
  private viewReportBtn: HTMLButtonElement;
  private settingsBtn: HTMLButtonElement;
  private currentSelection: SelectionResponse | null = null;
  private currentReport: IdeaReport | null = null;
  private pollInterval: ReturnType<typeof setInterval> | null = null;

  constructor() {
    this.statusEl = document.getElementById('status')!;
    this.selectionPreviewEl = document.getElementById('selection-preview')!;
    this.loadingEl = document.getElementById('loading')!;
    this.loadingTextEl = document.getElementById('loading-text')!;
    this.resultSummaryEl = document.getElementById('result-summary')!;
    this.resultTickersEl = document.getElementById('result-tickers')!;
    this.resultConfidenceEl = document.getElementById('result-confidence')!;
    this.generateBtn = document.getElementById('generate-btn') as HTMLButtonElement;
    this.cancelBtn = document.getElementById('cancel-btn') as HTMLButtonElement;
    this.viewReportBtn = document.getElementById('view-report-btn') as HTMLButtonElement;
    this.settingsBtn = document.getElementById('settings-btn') as HTMLButtonElement;
    this.bindEvents();
    this.init();
  }

  private bindEvents(): void {
    this.generateBtn.addEventListener('click', () => this.handleGenerate());
    this.cancelBtn.addEventListener('click', () => this.handleCancel());
    this.viewReportBtn.addEventListener('click', () => this.handleViewReport());
    this.settingsBtn.addEventListener('click', () => this.handleSettings());
  }

  private async init(): Promise<void> {
    const state = await this.getState();
    if (state.status === 'generating') {
      this.showGenerating(state.current_stage);
      this.startPolling();
    } else if (state.status === 'completed' && state.report) {
      this.showCompleted(state.report);
    } else if (state.status === 'failed' && state.error) {
      this.showError(state.error);
    }
    await this.checkSelection();
  }

  private async getState(): Promise<GenerationState> {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: 'GET_STATE' }, (response: GenerationState) => {
        resolve(response || { status: 'idle' });
      });
    });
  }

  private async checkSelection(): Promise<void> {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      this.setStatus('Cannot access this page', 'error');
      return;
    }

    try {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_SELECTION' });
      this.handleSelectionResponse(response as SelectionResponse);
    } catch {
      this.setStatus('Content script not loaded', 'error');
    }
  }

  private handleSelectionResponse(response: SelectionResponse): void {
    this.currentSelection = response;

    if (!response.valid) {
      this.generateBtn.disabled = true;
      this.selectionPreviewEl.classList.remove('visible');
      this.setStatus(response.error || 'Select text on the page to analyze');
      return;
    }

    this.generateBtn.disabled = false;
    this.selectionPreviewEl.textContent = response.text.substring(0, 200) + (response.text.length > 200 ? '...' : '');
    this.selectionPreviewEl.classList.add('visible');

    if (response.truncated) {
      const notice = document.createElement('div');
      notice.className = 'truncation-notice';
      notice.textContent = 'Text was truncated to 8,000 characters';
      this.selectionPreviewEl.appendChild(notice);
    }

    this.setStatus(`${response.text.length} characters selected`, 'success');
  }

  private async handleGenerate(): Promise<void> {
    if (!this.currentSelection?.valid) return;

    this.generateBtn.disabled = true;
    this.showGenerating('extraction');

    const response = await chrome.runtime.sendMessage({
      type: 'GENERATE',
      payload: {
        selection_text: this.currentSelection.text,
        url: this.currentSelection.url,
        title: this.currentSelection.title,
      },
    });

    if ((response as GenerationState).status === 'failed') {
      this.showError((response as GenerationState).error || 'Generation failed');
      return;
    }

    this.startPolling();
  }

  private async handleCancel(): Promise<void> {
    this.cancelBtn.disabled = true;
    await chrome.runtime.sendMessage({ type: 'CANCEL' });
    this.stopPolling();
    this.hideLoading();
    this.setStatus('Generation cancelled');
    this.generateBtn.disabled = false;
    this.cancelBtn.disabled = false;
  }

  private handleViewReport(): void {
    chrome.sidePanel.open({ windowId: chrome.windows.WINDOW_ID_CURRENT });
  }

  private handleSettings(): void {
    chrome.runtime.openOptionsPage();
  }

  private startPolling(): void {
    if (this.pollInterval) return;
    this.pollInterval = setInterval(() => this.pollState(), 1000);
  }

  private stopPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  private async pollState(): Promise<void> {
    const state = await this.getState();

    if (state.status === 'generating') {
      this.showGenerating(state.current_stage);
    } else if (state.status === 'completed' && state.report) {
      this.stopPolling();
      this.showCompleted(state.report);
    } else if (state.status === 'failed') {
      this.stopPolling();
      this.showError(state.error || 'Generation failed');
    }
  }

  private showGenerating(stage?: string): void {
    this.loadingEl.classList.remove('hidden');
    this.cancelBtn.classList.remove('hidden');
    this.generateBtn.classList.add('hidden');
    this.resultSummaryEl.classList.add('hidden');
    this.viewReportBtn.classList.add('hidden');
    this.loadingTextEl.textContent = STAGE_LABELS[stage || 'extraction'] || 'Processing...';
    this.setStatus('Generating investment idea...');
  }

  private hideLoading(): void {
    this.loadingEl.classList.add('hidden');
    this.cancelBtn.classList.add('hidden');
    this.generateBtn.classList.remove('hidden');
  }

  private showCompleted(report: IdeaReport): void {
    this.currentReport = report;
    this.hideLoading();
    this.resultSummaryEl.classList.remove('hidden');
    this.viewReportBtn.classList.remove('hidden');

    const tickers = report.tickers.map((t) => t.symbol).join(', ') || 'No tickers';
    this.resultTickersEl.textContent = `Tickers: ${tickers}`;
    this.resultConfidenceEl.textContent = `Confidence: ${Math.round(report.confidence_score * 100)}%`;

    this.setStatus('Analysis complete', 'success');
  }

  private showError(error: string): void {
    this.hideLoading();
    this.resultSummaryEl.classList.add('hidden');
    this.viewReportBtn.classList.add('hidden');
    this.generateBtn.disabled = false;

    if (error.includes('No provider configured')) {
      this.setStatus('Please configure a provider in settings', 'error');
      this.settingsBtn.classList.add('primary');
    } else if (error.includes('rate limit') || error.includes('429')) {
      const waitMatch = error.match(/(\d+)\s*seconds?/i);
      const waitTime = waitMatch ? waitMatch[1] : '60';
      this.setStatus(`Rate limited. Please wait ${waitTime} seconds and try again.`, 'error');
    } else if (error.includes('ECONNREFUSED') || error.includes('unreachable') || error.includes('ENOTFOUND')) {
      this.setStatus('Provider unreachable. Check your connection and settings.', 'error');
      this.generateBtn.textContent = 'Retry';
    } else if (error.includes('timeout') || error.includes('ETIMEDOUT')) {
      this.setStatus('Request timed out. Try again with shorter text.', 'error');
    } else if (error.includes('invalid_api_key') || error.includes('401')) {
      this.setStatus('Invalid API key. Please check your settings.', 'error');
      this.settingsBtn.classList.add('primary');
    } else {
      this.setStatus(error, 'error');
    }
  }

  private setStatus(message: string, type?: 'error' | 'success'): void {
    this.statusEl.textContent = message;
    this.statusEl.className = 'status';
    if (type) {
      this.statusEl.classList.add(type);
    }
  }
}

new PopupController();
