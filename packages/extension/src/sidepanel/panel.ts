import type { AgentResult, ChatMessage, Evaluation, GenerationState, IdeaReport, NewsItem, FundamentalsSnapshot, AgentMessage, ThinkingChunk, Recommendation, RelatedTicker, UserTicker, QuantitativeEntry } from '../types';
import { getReports, getEvaluations, getSettings, saveSettings, searchReports, saveEvaluation } from '../lib/storage';
import { chatWithReport, searchTickers, TickerSearchResult } from '../lib/api';
import { generateMarkdown, generateJSON, downloadFile } from '../lib/export';

const LANGUAGE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'en', label: 'English' },
  { value: 'ko', label: 'Korean' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'hi', label: 'Hindi' },
  { value: 'ar', label: 'Arabic' },
];

interface TickerChip {
  symbol: string;
  isValid: boolean;
}

class PanelController {
  private contentEl: HTMLElement;
  private emptyStateEl: HTMLElement;
  private reportViewEl: HTMLElement;
  private historyViewEl: HTMLElement;
  private tabReportBtn: HTMLButtonElement;
  private tabHistoryBtn: HTMLButtonElement;
  private chatInput!: HTMLInputElement;
  private chatSendBtn!: HTMLButtonElement;
  private chatMessagesEl!: HTMLElement;
  private currentReport: IdeaReport | null = null;
  private evaluations: Map<string, Evaluation> = new Map();
  private chatMessages: ChatMessage[] = [];
  private chatReportId: string | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private elapsedTimer: ReturnType<typeof setInterval> | null = null;
  private generationStartedAt: string | null = null;
  private thinkingRafId: number | null = null;
  private pendingThinkingUpdate = false;
  private userScrolledUp = false;
  private userTickers: TickerChip[] = [];
  private tickerInputEl: HTMLInputElement | null = null;
  private tickerChipsEl: HTMLElement | null = null;
  private currentSelection: { text: string; url: string; title: string } | null = null;
  private suggestions: TickerSearchResult[] = [];
  private selectedSuggestionIndex = -1;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private suggestionsEl: HTMLElement | null = null;
  private selectedLanguage: string = 'auto';

  constructor() {
    this.contentEl = document.getElementById('content')!;
    this.emptyStateEl = document.getElementById('empty-state')!;
    this.reportViewEl = document.getElementById('report-view')!;
    this.historyViewEl = document.getElementById('history-view')!;
    this.tabReportBtn = document.getElementById('tab-report') as HTMLButtonElement;
    this.tabHistoryBtn = document.getElementById('tab-history') as HTMLButtonElement;
    this.bindEvents();
    this.listenForStateChanges();
    this.init();
  }

  private bindEvents(): void {
    this.tabReportBtn.addEventListener('click', () => this.showTab('report'));
    this.tabHistoryBtn.addEventListener('click', () => this.showTab('history'));
    this.listenForSelectionChanges();
  }

  private listenForSelectionChanges(): void {
    chrome.runtime.onMessage.addListener((message) => {
      if (message.type === 'SELECTION_CHANGED') {
        this.currentSelection = { text: message.payload.text, url: message.payload.url, title: message.payload.title };
        this.showSelectionUI();
      } else if (message.type === 'SELECTION_CLEARED') {
        this.currentSelection = null;
        this.hideSelectionUI();
      }
    });
  }

  private showSelectionUI(): void {
    if (!this.currentSelection) return;
    let container = document.getElementById('selection-ui');
    if (!container) {
      container = document.createElement('div');
      container.id = 'selection-ui';
      container.innerHTML = `
        <style>
          #selection-ui { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px; padding: 16px 20px; }
          .selection-preview { font-size: 13px; color: #6b7280; margin-bottom: 12px; max-height: 60px; overflow: hidden; text-overflow: ellipsis; }
          .ticker-input-container { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px; border: 1px solid #d1d5db; border-radius: 8px; background: #f9fafb; min-height: 38px; align-items: center; margin-bottom: 12px; }
          .ticker-chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: #eff6ff; border-radius: 12px; font-size: 12px; font-weight: 500; color: #2563eb; }
          .ticker-chip.invalid { background: #fee2e2; color: #991b1b; }
          .ticker-chip-remove { cursor: pointer; font-size: 14px; line-height: 1; opacity: 0.7; }
          .ticker-chip-remove:hover { opacity: 1; }
          .ticker-input { border: none; outline: none; background: transparent; font-size: 13px; flex: 1; min-width: 80px; }
          .ticker-input::placeholder { color: #9ca3af; }
          .generate-btn { width: 100%; padding: 10px 16px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; }
          .generate-btn:hover { background: #1d4ed8; }
          .generate-btn:disabled { background: #9ca3af; cursor: not-allowed; }
          .ticker-label { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
          .ticker-suggestions { position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #d1d5db; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 100; max-height: 200px; overflow-y: auto; margin-top: 4px; }
          .ticker-suggestion { padding: 10px 12px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
          .ticker-suggestion:hover, .ticker-suggestion.selected { background: #f3f4f6; }
          .ticker-suggestion-symbol { font-weight: 600; color: #2563eb; }
          .ticker-suggestion-name { font-size: 12px; color: #6b7280; flex: 1; margin-left: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
          .ticker-suggestion-exchange { font-size: 11px; color: #9ca3af; }
          .ticker-input-wrapper { position: relative; }
          .language-row { display: flex; gap: 8px; align-items: center; }
          .language-select { flex: 0 0 auto; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; background: #fff; cursor: pointer; min-width: 120px; }
          .language-select:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,0.2); }
        </style>
        <div class="selection-preview" id="selection-preview"></div>
        <div class="ticker-label">Add tickers (optional)</div>
        <div class="ticker-input-wrapper">
          <div class="ticker-input-container" id="ticker-chips">
            <input type="text" class="ticker-input" id="ticker-input" placeholder="e.g., AAPL or Apple..." autocomplete="off" />
          </div>
          <div class="ticker-suggestions hidden" id="ticker-suggestions"></div>
        </div>
        <div class="language-row">
          <select class="language-select" id="language-select">
            ${LANGUAGE_OPTIONS.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
          </select>
          <button class="generate-btn" id="generate-btn">Generate Report</button>
        </div>
      `;
      this.contentEl.insertBefore(container, this.contentEl.firstChild);
    }
    const preview = document.getElementById('selection-preview');
    if (preview) preview.textContent = this.currentSelection.text.slice(0, 150) + (this.currentSelection.text.length > 150 ? '...' : '');
    this.tickerInputEl = document.getElementById('ticker-input') as HTMLInputElement;
    this.tickerChipsEl = document.getElementById('ticker-chips');
    this.bindTickerInputEvents();
    this.bindGenerateButton();
    this.bindLanguagePicker();
    container.classList.remove('hidden');
  }

  private hideSelectionUI(): void {
    const container = document.getElementById('selection-ui');
    if (container) container.classList.add('hidden');
  }

  private bindTickerInputEvents(): void {
    if (!this.tickerInputEl) return;
    this.suggestionsEl = document.getElementById('ticker-suggestions');
    this.tickerInputEl.addEventListener('keydown', (e) => {
      if (this.suggestions.length > 0) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.selectedSuggestionIndex = Math.min(this.selectedSuggestionIndex + 1, this.suggestions.length - 1);
          this.renderSuggestions();
          return;
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          this.selectedSuggestionIndex = Math.max(this.selectedSuggestionIndex - 1, -1);
          this.renderSuggestions();
          return;
        } else if (e.key === 'Enter' && this.selectedSuggestionIndex >= 0) {
          e.preventDefault();
          this.selectSuggestion(this.suggestions[this.selectedSuggestionIndex]);
          return;
        } else if (e.key === 'Escape') {
          this.hideSuggestions();
          return;
        }
      }
      if (e.key === 'Enter' || e.key === ',' || e.key === 'Tab') {
        e.preventDefault();
        this.addTickerFromInput();
      } else if (e.key === 'Backspace' && !this.tickerInputEl!.value && this.userTickers.length > 0) {
        this.removeTicker(this.userTickers.length - 1);
      }
    });
    this.tickerInputEl.addEventListener('input', () => this.onTickerInputChange());
    this.tickerInputEl.addEventListener('blur', () => {
      setTimeout(() => this.hideSuggestions(), 150);
      this.addTickerFromInput();
    });
  }

  private onTickerInputChange(): void {
    const query = this.tickerInputEl?.value.trim() || '';
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    if (query.length < 2) {
      this.hideSuggestions();
      return;
    }
    this.debounceTimer = setTimeout(() => this.fetchSuggestions(query), 300);
  }

  private async fetchSuggestions(query: string): Promise<void> {
    try {
      const results = await searchTickers(query);
      this.suggestions = results;
      this.selectedSuggestionIndex = -1;
      if (results.length > 0) {
        this.renderSuggestions();
        this.suggestionsEl?.classList.remove('hidden');
      } else {
        this.hideSuggestions();
      }
    } catch {
      this.hideSuggestions();
    }
  }

  private renderSuggestions(): void {
    if (!this.suggestionsEl) return;
    this.suggestionsEl.innerHTML = this.suggestions.map((s, i) => `
      <div class="ticker-suggestion${i === this.selectedSuggestionIndex ? ' selected' : ''}" data-index="${i}">
        <span class="ticker-suggestion-symbol">${this.escapeHtml(s.symbol)}</span>
        <span class="ticker-suggestion-name">${this.escapeHtml(s.name)}</span>
        <span class="ticker-suggestion-exchange">${this.escapeHtml(s.exchange)}</span>
      </div>
    `).join('');
    this.suggestionsEl.querySelectorAll('.ticker-suggestion').forEach((el) => {
      el.addEventListener('mousedown', (e) => {
        e.preventDefault();
        const index = parseInt(el.getAttribute('data-index') || '0');
        this.selectSuggestion(this.suggestions[index]);
      });
    });
  }

  private selectSuggestion(suggestion: TickerSearchResult): void {
    this.addTicker(suggestion.symbol);
    this.userTickers[this.userTickers.length - 1] = { symbol: suggestion.symbol, isValid: true };
    if (this.tickerInputEl) this.tickerInputEl.value = '';
    this.renderTickerChips();
    this.hideSuggestions();
    this.tickerInputEl?.focus();
  }

  private hideSuggestions(): void {
    this.suggestions = [];
    this.selectedSuggestionIndex = -1;
    this.suggestionsEl?.classList.add('hidden');
  }

  private bindGenerateButton(): void {
    const btn = document.getElementById('generate-btn');
    btn?.addEventListener('click', () => this.triggerGenerate());
  }

  private async bindLanguagePicker(): Promise<void> {
    const select = document.getElementById('language-select') as HTMLSelectElement;
    if (!select) return;
    const settings = await getSettings();
    if (settings?.output_language) {
      select.value = settings.output_language;
      this.selectedLanguage = settings.output_language;
    }
    select.addEventListener('change', async () => {
      this.selectedLanguage = select.value;
      const currentSettings = await getSettings();
      if (currentSettings) {
        currentSettings.output_language = select.value;
        await saveSettings(currentSettings);
      }
    });
  }

  private addTickerFromInput(): void {
    if (!this.tickerInputEl) return;
    const raw = this.tickerInputEl.value.trim();
    if (!raw) return;
    const symbols = raw.split(',').map((s) => s.trim().toUpperCase()).filter((s) => s);
    for (const symbol of symbols) {
      this.addTicker(symbol);
    }
    this.tickerInputEl.value = '';
    this.renderTickerChips();
  }

  private addTicker(symbol: string): void {
    const normalized = symbol.toUpperCase().trim();
    if (!normalized) return;
    if (this.userTickers.some((t) => t.symbol === normalized)) return;
    const isValid = /^[A-Z0-9.\-]{1,12}$/.test(normalized);
    this.userTickers.push({ symbol: normalized, isValid });
  }

  private removeTicker(index: number): void {
    this.userTickers.splice(index, 1);
    this.renderTickerChips();
  }

  private renderTickerChips(): void {
    if (!this.tickerChipsEl || !this.tickerInputEl) return;
    const existingChips = this.tickerChipsEl.querySelectorAll('.ticker-chip');
    existingChips.forEach((chip) => chip.remove());
    for (let i = 0; i < this.userTickers.length; i++) {
      const chip = this.userTickers[i];
      const el = document.createElement('span');
      el.className = `ticker-chip${chip.isValid ? '' : ' invalid'}`;
      el.innerHTML = `${this.escapeHtml(chip.symbol)} <span class="ticker-chip-remove" data-index="${i}">&times;</span>`;
      this.tickerChipsEl.insertBefore(el, this.tickerInputEl);
    }
    this.tickerChipsEl.querySelectorAll('.ticker-chip-remove').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const index = parseInt((e.target as HTMLElement).getAttribute('data-index') || '0');
        this.removeTicker(index);
      });
    });
    this.updateGenerateButtonState();
  }

  private updateGenerateButtonState(): void {
    const btn = document.getElementById('generate-btn') as HTMLButtonElement;
    if (!btn) return;
    const hasInvalid = this.userTickers.some((t) => !t.isValid);
    btn.disabled = hasInvalid;
    btn.title = hasInvalid ? 'Fix invalid tickers before generating' : '';
  }

  private async triggerGenerate(): Promise<void> {
    if (!this.currentSelection) return;
    const hasInvalid = this.userTickers.some((t) => !t.isValid);
    if (hasInvalid) return;
    const userTickers: UserTicker[] = this.userTickers.filter((t) => t.isValid).map((t) => ({ symbol: t.symbol }));
    await chrome.runtime.sendMessage({
      type: 'GENERATE',
      payload: {
        selection_text: this.currentSelection.text,
        url: this.currentSelection.url,
        title: this.currentSelection.title,
        user_tickers: userTickers.length > 0 ? userTickers : undefined,
      },
    });
    this.userTickers = [];
    this.renderTickerChips();
    this.hideSelectionUI();
  }

  private async init(): Promise<void> {
    const evals = await getEvaluations();
    evals.forEach((e) => this.evaluations.set(e.idea_id, e));
    this.startPolling();
    const state = await this.getState();
    if (state.status === 'completed' && state.report) {
      this.stopPolling();
      this.currentReport = state.report;
      this.renderReport(state.report);
      this.showTab('report');
    } else if (state.status === 'generating') {
      this.renderProgress(state);
    } else {
      await this.loadHistory();
    }
    const result = await chrome.storage.local.get('current_selection');
    if (result.current_selection) {
      this.currentSelection = result.current_selection;
      this.showSelectionUI();
    }
  }

  private static readonly STAGE_LABELS: Record<string, string> = {
    extraction: 'Extracting text',
    entity: 'Identifying entities',
    ticker: 'Mapping tickers',
    thesis: 'Generating thesis',
    critique: 'Analyzing risks',
    confidence: 'Scoring confidence',
    discovery: 'Discovering related tickers',
    enrichment: 'Data agents',
    recommendation: 'Generating recommendations',
    formatting: 'Formatting report',
  };

  private static readonly AGENT_LABELS: Record<string, string> = {
    news_agent: 'News Agent',
    fundamentals_agent: 'Fundamentals Agent',
    risk_agent: 'Risk Agent',
    macro_agent: 'Macro Agent',
    synthesis_agent: 'Synthesis Agent',
  };

  private static readonly PIPELINE_STAGES = [
    'extraction', 'entity', 'ticker', 'thesis', 'critique', 'confidence', 'discovery', 'enrichment', 'recommendation', 'formatting',
  ];

  private renderProgress(state: GenerationState): void {
    this.emptyStateEl.classList.add('hidden');
    this.historyViewEl.classList.add('hidden');
    this.reportViewEl.classList.remove('hidden');

    const completed = state.completed_stages || [];
    const enrichmentAgents = state.enrichment_agents || [];
    const currentStage = state.current_stage || '';
    const results = state.agent_results || [];

    const retryInfo = new Map<string, string>();
    for (const s of completed) {
      if (s.startsWith('retry:')) {
        const parts = s.split(':');
        retryInfo.set(parts[1], `(attempt ${parseInt(parts[2]) + 1}/${parts[3]})`);
      }
    }

    const mainStage = currentStage.startsWith('retry:') ? currentStage.split(':')[1]
      : currentStage.startsWith('result:') ? currentStage.split(':')[1]
      : currentStage.startsWith('enrichment:') ? 'enrichment'
      : currentStage;
    const stagesHtml = PanelController.PIPELINE_STAGES.map((stage) => {
      const isDone = completed.includes(stage) && (stage !== 'enrichment' || completed.includes('formatting'));
      const isCurrent = !isDone && (stage === mainStage);
      const icon = isDone ? '<span class="stage-icon done">&#10003;</span>'
        : isCurrent ? '<span class="stage-icon current"><span class="spinner-sm"></span></span>'
        : '<span class="stage-icon pending">&#9675;</span>';
      const retry = retryInfo.get(stage);
      const label = (PanelController.STAGE_LABELS[stage] || stage) + (retry && isCurrent ? ` <span class="retry-badge">${retry}</span>` : '');
      const cls = isDone ? 'done' : isCurrent ? 'current' : 'pending';
      const resultPreview = this.renderResultPreview(stage, results);

      let agentSublist = '';
      if (stage === 'enrichment' && enrichmentAgents.length > 0) {
        agentSublist = '<ul class="agent-progress">' + enrichmentAgents.map((agentId) => {
          const agentDone = completed.includes(`agent:${agentId}`);
          const agentActive = !agentDone && (mainStage === 'enrichment' || completed.includes('enrichment'));
          const aIcon = agentDone ? '<span class="stage-icon done">&#10003;</span>'
            : agentActive ? '<span class="stage-icon current"><span class="spinner-sm"></span></span>'
            : '<span class="stage-icon pending">&#9675;</span>';
          const aLabel = PanelController.AGENT_LABELS[agentId] || agentId;
          const aCls = agentDone ? 'done' : agentActive ? 'current' : 'pending';
          const agentPreview = this.renderResultPreview(agentId, results);
          return `<li class="stage-item ${aCls}">${aIcon} ${aLabel}${agentPreview}</li>`;
        }).join('') + this.renderSequentialAgents(completed, currentStage, enrichmentAgents, results) + '</ul>';
      }

      return `<li class="stage-item ${cls}">${icon} ${label}${resultPreview}${agentSublist}</li>`;
    }).join('');

    const thinkingChunks = state.thinking_chunks || [];
    const thinkingHtml = thinkingChunks.length > 0 ? this.renderThinking(thinkingChunks) : '';
    const stageLabel = PanelController.STAGE_LABELS[mainStage] || PanelController.AGENT_LABELS[mainStage] || mainStage || 'Starting';

    this.reportViewEl.innerHTML = `
      <div class="progress-view">
        <h2>Generating Report</h2>
        <div class="progress-status">
          <span class="progress-pulse"></span>
          <span class="progress-label">${stageLabel}</span>
          <span class="progress-elapsed" id="elapsed-time"></span>
        </div>
        <ul class="stage-list">${stagesHtml}</ul>
        ${thinkingHtml}
      </div>
    `;
    this.generationStartedAt = state.started_at || null;
    this.startElapsedTimer();
    this.bindThinkingScroll();
    this.tabReportBtn.classList.add('active');
    this.tabHistoryBtn.classList.remove('active');
  }

  private startElapsedTimer(): void {
    this.stopElapsedTimer();
    this.updateElapsed();
    this.elapsedTimer = setInterval(() => this.updateElapsed(), 1000);
  }

  private stopElapsedTimer(): void {
    if (this.elapsedTimer) {
      clearInterval(this.elapsedTimer);
      this.elapsedTimer = null;
    }
  }

  private updateElapsed(): void {
    const el = document.getElementById('elapsed-time');
    if (!el || !this.generationStartedAt) return;
    const elapsed = Math.floor((Date.now() - new Date(this.generationStartedAt).getTime()) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    el.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  private renderSequentialAgents(completed: string[], currentStage: string, _parallelAgents: string[], results: AgentResult[]): string {
    const sequential = ['risk_agent', 'synthesis_agent'];
    return sequential.map((agentId) => {
      const done = completed.includes(`agent:${agentId}`) || completed.includes(`enrichment:${agentId}`);
      const active = !done && (currentStage === `enrichment:${agentId}` || currentStage === `enrichment:risk_agent,synthesis_agent`);
      const icon = done ? '<span class="stage-icon done">&#10003;</span>'
        : active ? '<span class="stage-icon current"><span class="spinner-sm"></span></span>'
        : '<span class="stage-icon pending">&#9675;</span>';
      const label = PanelController.AGENT_LABELS[agentId] || agentId;
      const cls = done ? 'done' : active ? 'current' : 'pending';
      const preview = this.renderResultPreview(agentId, results);
      return `<li class="stage-item ${cls}">${icon} ${label}${preview}</li>`;
    }).join('');
  }

  private renderResultPreview(agentId: string, results: AgentResult[]): string {
    const result = results.find((r) => r.agent_id === agentId);
    if (!result) return '';
    const s = result.summary;
    const lines: string[] = [];
    if (agentId === 'extraction') {
      if (s.language) lines.push(`Language: ${s.language}`);
    } else if (agentId === 'entity') {
      const companies = s.companies as string[] | undefined;
      if (companies?.length) lines.push(companies.join(', '));
    } else if (agentId === 'ticker') {
      const tickers = s.tickers as Array<{ symbol: string; confidence: number }> | undefined;
      if (tickers?.length) lines.push(tickers.map((t) => `${t.symbol} (${Math.round(t.confidence * 100)}%)`).join(', '));
    } else if (agentId === 'thesis') {
      const thesis = s.thesis as string || '';
      if (thesis) lines.push(thesis.slice(0, 200) + (thesis.length > 200 ? '...' : ''));
      const catalysts = s.catalysts as string[] | undefined;
      if (catalysts?.length) lines.push(`Catalysts: ${catalysts.join('; ')}`);
      if (s.horizon) lines.push(`Horizon: ${s.horizon}`);
    } else if (agentId === 'critique') {
      const risks = s.risks as string[] | undefined;
      if (risks?.length) {
        for (const r of risks.slice(0, 2)) lines.push(`• ${r.slice(0, 100)}${r.length > 100 ? '...' : ''}`);
        if ((s.risks_count as number) > 2) lines.push(`+ ${(s.risks_count as number) - 2} more`);
      }
      const ct = s.counter_thesis as string | undefined;
      if (ct) lines.push(`Counter: ${ct.slice(0, 120)}${ct.length > 120 ? '...' : ''}`);
    } else if (agentId === 'confidence') {
      lines.push(`Score: ${Math.round((s.score as number || 0) * 100)}%`);
      const expl = s.explanation as string | undefined;
      if (expl) lines.push(expl.slice(0, 150) + (expl.length > 150 ? '...' : ''));
    } else if (agentId === 'news_agent') {
      const headlines = s.headlines as string[] | undefined;
      if (headlines?.length) {
        for (const h of headlines) lines.push(`• ${h}`);
      } else {
        lines.push(`${s.count || 0} articles`);
      }
    } else if (agentId === 'fundamentals_agent') {
      const metrics = s.metrics as Array<{ name: string; value: string }> | undefined;
      if (metrics?.length) lines.push(metrics.map((m) => `${m.name}: ${m.value}`).join(' · '));
    } else if (agentId === 'macro_agent') {
      let t = `${s.sector || ''}`;
      if (s.tailwinds || s.headwinds) t += ` — ${s.tailwinds} tailwinds, ${s.headwinds} headwinds`;
      lines.push(t);
    } else if (agentId === 'risk_agent') {
      if (s.top_risk) lines.push(`${s.risks_count} risks — ${(s.top_risk as string).slice(0, 80)}`);
    } else if (agentId === 'discovery') {
      const companies = s.companies as Array<{ symbol: string; name: string; relationship: string }> | undefined;
      if (companies?.length) {
        for (const c of companies) lines.push(`${c.symbol} (${c.name}) — ${c.relationship}`);
      } else {
        lines.push(`${s.related_count || 0} related tickers`);
      }
    } else if (agentId === 'recommendation') {
      const signals = s.signals as Array<{ symbol: string; signal: string; certainty: number }> | undefined;
      if (signals?.length) {
        lines.push(signals.map((r) => `${r.symbol}: ${r.signal} ${Math.round(r.certainty * 100)}%`).join(', '));
      } else {
        lines.push(`${s.count || 0} recommendations`);
      }
    }
    if (!lines.length) return '';
    const escaped = lines.map((l) => this.escapeHtml(l));
    return `<div class="result-preview">${escaped.join('<br/>')}</div>`;
  }

  private static readonly THINKING_MAX_CHARS = 50000;

  private renderThinking(chunks: ThinkingChunk[]): string {
    const parallel = chunks.filter((c) => c.phase === 'parallel');
    const sequential = chunks.filter((c) => c.phase === 'sequential');
    let html = '<div class="thinking-section">';
    if (parallel.length > 0) {
      html += '<div class="thinking-phase-group"><div class="thinking-phase-label">Parallel Analysis</div>';
      for (const chunk of parallel) {
        const label = PanelController.AGENT_LABELS[chunk.agent_id] || chunk.agent_id;
        const truncated = chunk.content.length > PanelController.THINKING_MAX_CHARS;
        const content = truncated ? chunk.content.slice(0, PanelController.THINKING_MAX_CHARS) : chunk.content;
        html += `<details class="thinking-agent" open><summary>${this.escapeHtml(label)}</summary>`;
        html += `<pre class="thinking-content">${this.escapeHtml(content)}</pre>`;
        if (truncated) html += '<div class="thinking-truncated">[Thinking truncated]</div>';
        html += '</details>';
      }
      html += '</div>';
    }
    for (const chunk of sequential) {
      const label = PanelController.AGENT_LABELS[chunk.agent_id] || chunk.agent_id;
      const truncated = chunk.content.length > PanelController.THINKING_MAX_CHARS;
      const content = truncated ? chunk.content.slice(0, PanelController.THINKING_MAX_CHARS) : chunk.content;
      html += `<details class="thinking-agent" open><summary>${this.escapeHtml(label)}</summary>`;
      html += `<pre class="thinking-content">${this.escapeHtml(content)}</pre>`;
      if (truncated) html += '<div class="thinking-truncated">[Thinking truncated]</div>';
      html += '</details>';
    }
    html += '</div>';
    return html;
  }

  private bindThinkingScroll(): void {
    const section = this.reportViewEl.querySelector('.thinking-section');
    if (!section) return;
    section.addEventListener('scroll', () => {
      const el = section as HTMLElement;
      this.userScrolledUp = el.scrollTop + el.clientHeight < el.scrollHeight - 20;
    });
    if (!this.userScrolledUp) {
      section.scrollTop = section.scrollHeight;
    }
  }

  private listenForStateChanges(): void {
    chrome.storage.onChanged.addListener((changes, areaName) => {
      if (areaName !== 'local' || !changes.generation_state) return;
      const state = changes.generation_state.newValue as GenerationState;
      if (!state) return;
      if (state.status === 'completed' && state.report) {
        this.stopElapsedTimer();
        this.currentReport = state.report;
        this.renderReport(state.report);
        this.showTab('report');
      } else if (state.status === 'failed') {
        this.stopElapsedTimer();
        this.reportViewEl.innerHTML = `
          <div class="empty-state">
            <h2>Generation Failed</h2>
            <p>${state.error || 'Unknown error'}</p>
          </div>
        `;
        this.emptyStateEl.classList.add('hidden');
        this.reportViewEl.classList.remove('hidden');
      } else if (state.status === 'generating') {
        this.renderProgress(state);
        if (!this.pollTimer) this.startPolling();
      }
    });
  }

  private startPolling(): void {
    this.stopPolling();
    this.pollTimer = setInterval(async () => {
      const state = await this.getState();
      if (state.status === 'completed' && state.report) {
        this.stopPolling();
        this.stopElapsedTimer();
        this.currentReport = state.report;
        this.renderReport(state.report);
      } else if (state.status === 'failed') {
        this.stopPolling();
        this.stopElapsedTimer();
        this.reportViewEl.innerHTML = `
          <div class="empty-state">
            <h2>Generation Failed</h2>
            <p>${state.error || 'Unknown error'}</p>
          </div>
        `;
      } else if (state.status === 'generating') {
        this.renderProgress(state);
      }
    }, 1000);
  }

  private stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  private async getState(): Promise<GenerationState> {
    const result = await chrome.storage.local.get('generation_state');
    return result.generation_state || { status: 'idle' };
  }

  private showTab(tab: 'report' | 'history'): void {
    this.tabReportBtn.classList.toggle('active', tab === 'report');
    this.tabHistoryBtn.classList.toggle('active', tab === 'history');
    this.emptyStateEl.classList.add('hidden');
    this.reportViewEl.classList.add('hidden');
    this.historyViewEl.classList.add('hidden');
    if (tab === 'report') {
      if (this.currentReport) {
        this.reportViewEl.classList.remove('hidden');
      } else {
        this.emptyStateEl.classList.remove('hidden');
      }
    } else if (tab === 'history') {
      this.historyViewEl.classList.remove('hidden');
      this.loadHistory();
    }
  }

  private initChat(): void {
    if (!this.currentReport) return;
    if (this.chatReportId !== this.currentReport.id) {
      if (this.chatReportId && this.chatMessages.length > 0) {
        this.chatMessagesEl.innerHTML = '';
        this.appendChatBubble('system', 'Chat cleared — you switched to a different report.');
      }
      this.chatMessages = [];
      this.chatReportId = this.currentReport.id;
    }
  }

  private bindInlineChat(): void {
    this.chatInput = document.getElementById('chat-input') as HTMLInputElement;
    this.chatSendBtn = document.getElementById('chat-send') as HTMLButtonElement;
    this.chatMessagesEl = document.getElementById('chat-messages')!;
    const toggle = document.getElementById('chat-toggle');
    const chatEl = document.getElementById('inline-chat');
    toggle?.addEventListener('click', () => chatEl?.classList.toggle('collapsed'));
    this.chatSendBtn.addEventListener('click', () => this.sendMessage());
    this.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !this.chatSendBtn.disabled) this.sendMessage();
    });
    this.chatInput.addEventListener('input', () => {
      this.chatSendBtn.disabled = !this.chatInput.value.trim();
    });
    this.initChat();
  }

  private appendChatBubble(type: 'user' | 'assistant' | 'system' | 'error', content: string, retryBtn = false): HTMLElement {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${type}`;
    bubble.textContent = content;
    if (retryBtn) {
      const btn = document.createElement('button');
      btn.textContent = 'Retry';
      btn.addEventListener('click', () => {
        bubble.remove();
        this.sendMessage(true);
      });
      bubble.appendChild(btn);
    }
    this.chatMessagesEl.appendChild(bubble);
    this.chatMessagesEl.scrollTop = this.chatMessagesEl.scrollHeight;
    this.applyRtl(this.chatMessagesEl);
    return bubble;
  }

  private showTypingIndicator(): HTMLElement {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
    this.chatMessagesEl.appendChild(indicator);
    this.chatMessagesEl.scrollTop = this.chatMessagesEl.scrollHeight;
    return indicator;
  }

  private buildReportContext(): Record<string, unknown> {
    const r = this.currentReport!;
    const ctx: Record<string, unknown> = {
      id: r.id,
      tickers: r.tickers,
      thesis: r.thesis,
      executive_summary: r.executive_summary,
      risks: r.risks,
      counter_thesis: r.counter_thesis,
      confidence_score: r.confidence_score,
      confidence_explanation: r.confidence_explanation,
      catalysts: r.catalysts,
      limitations: r.limitations,
    };
    if (r.news_context?.length) {
      ctx.news_context = r.news_context.map((n) => `${n.headline} (${n.source})`).join('; ');
    }
    if (r.fundamentals_summary?.length) {
      ctx.fundamentals_summary = r.fundamentals_summary.map((f) =>
        `${f.ticker}: ${f.metrics.map((m) => `${m.name}=${m.value}`).join(', ')}`
      ).join('; ');
    }
    if (r.macro_context) {
      ctx.macro_context = `Sector: ${r.macro_context.sector}. Tailwinds: ${r.macro_context.tailwinds.join(', ')}. Headwinds: ${r.macro_context.headwinds.join(', ')}`;
    }
    return ctx;
  }

  private async sendMessage(retry = false): Promise<void> {
    const text = retry
      ? this.chatMessages.filter((m) => m.role === 'user').pop()?.content || ''
      : this.chatInput.value.trim();
    if (!text || !this.currentReport) return;
    if (!retry) {
      this.chatInput.value = '';
      this.chatSendBtn.disabled = true;
      const msg: ChatMessage = { role: 'user', content: text, timestamp: new Date().toISOString() };
      this.chatMessages.push(msg);
      this.appendChatBubble('user', text);
    }
    this.chatSendBtn.disabled = true;
    this.chatInput.disabled = true;
    const indicator = this.showTypingIndicator();
    try {
      const settings = await getSettings();
      if (!settings) throw new Error('Settings not found');
      const response = await chatWithReport(
        this.buildReportContext(),
        this.chatMessages.map((m) => ({ role: m.role, content: m.content })),
        settings
      );
      indicator.remove();
      const assistantMsg: ChatMessage = { role: 'assistant', content: response.content, timestamp: response.timestamp };
      this.chatMessages.push(assistantMsg);
      this.appendChatBubble('assistant', response.content);
    } catch (e) {
      indicator.remove();
      this.appendChatBubble('error', 'Failed to get response', true);
    } finally {
      this.chatInput.disabled = false;
      this.chatSendBtn.disabled = !this.chatInput.value.trim();
      this.chatInput.focus();
    }
  }

  private async applyRtl(el: HTMLElement): Promise<void> {
    const settings = await getSettings();
    el.classList.toggle('rtl', settings?.output_language === 'ar');
  }

  private async loadHistory(): Promise<void> {
    const reports = await getReports();
    this.renderHistory(reports);
  }

  private renderHistory(reports: IdeaReport[]): void {
    if (reports.length === 0) {
      this.historyViewEl.innerHTML = `
        <div class="empty-state">
          <h2>No History</h2>
          <p>Your generated reports will appear here.</p>
        </div>
      `;
      return;
    }

    this.historyViewEl.innerHTML = reports
      .map(
        (report) => `
      <div class="history-item" data-id="${report.id}">
        <div class="history-item-title">${this.escapeHtml(report.source.title || 'Untitled')}</div>
        <div class="history-item-meta">
          ${report.tickers.map((t) => t.symbol).join(', ') || 'No tickers'} • ${this.formatDate(report.created_at)}
        </div>
      </div>
    `
      )
      .join('');

    this.historyViewEl.querySelectorAll('.history-item').forEach((item) => {
      item.addEventListener('click', () => {
        const id = item.getAttribute('data-id');
        const report = reports.find((r) => r.id === id);
        if (report) {
          this.currentReport = report;
          this.renderReport(report);
          this.showTab('report');
        }
      });
    });
  }

  private renderReport(report: IdeaReport): void {
    const evaluation = this.evaluations.get(report.id);
    this.reportViewEl.innerHTML = `
      <div class="report-header">
        <div class="report-title">${this.escapeHtml(report.source.title || 'Investment Analysis')}</div>
        <div class="report-meta">
          <a href="${this.escapeHtml(report.source.url)}" target="_blank">${this.truncateUrl(report.source.url)}</a>
          • ${this.formatDate(report.created_at)}
        </div>
      </div>
      <div class="disclaimer">
        ${this.escapeHtml(report.disclaimer || 'AI-generated analysis for educational purposes only. Not professional financial advice.')}
      </div>
      ${this.renderSection('Executive Summary', this.renderExecutiveSummary(report.executive_summary))}
      ${this.renderSection('Tickers', this.renderTickers(report.tickers))}
      ${report.related_tickers?.length ? this.renderSection('Related Tickers', this.renderRelatedTickers(report.related_tickers)) : ''}
      ${this.renderSection('Investment Thesis', `<div class="thesis">${this.escapeHtml(report.thesis)}</div>`)}
      ${this.renderSection('Supporting Quotes', this.renderQuotes(report.rationale_quotes))}
      ${this.renderSection('Catalysts', this.renderList(report.catalysts))}
      ${this.renderSection('Risks', this.renderList(report.risks, 'risks'))}
      ${this.renderSection('Counter-Thesis', `<div class="counter-thesis">${this.escapeHtml(report.counter_thesis)}</div>`)}
      ${report.quantitative_data?.length ? this.renderSection('Quantitative Metrics', this.renderQuantitativeData(report.quantitative_data)) : ''}
      ${report.confidence_score != null ? this.renderSection('Confidence', this.renderConfidence(report), true) : ''}
      ${this.renderSection('Time Horizon', `<span class="horizon">${report.horizon}</span>`)}
      ${this.renderSection('Limitations', this.renderList(report.limitations))}
      ${report.news_context?.length ? this.renderSection('News Context', this.renderNewsContext(report.news_context, report.agent_attributions), false) : ''}
      ${report.fundamentals_summary?.length ? this.renderSection('Fundamentals', this.renderFundamentals(report.fundamentals_summary, report.agent_attributions), false) : ''}
      ${report.cross_reference_analysis ? this.renderSection('Cross-Reference Analysis', this.renderCrossReference(report.cross_reference_analysis), false) : ''}
      ${report.macro_context ? this.renderSection('Macro Context', this.renderMacroContext(report.macro_context), false) : ''}
      ${report.thinking_output ? this.renderSection('Thinking Process', this.renderThinkingOutput(report.thinking_output), true) : ''}
      ${report.communication_log?.messages?.length ? this.renderSection('Agent Log', this.renderCommunicationLog(report.communication_log.messages), true) : ''}
      ${this.renderSection('Provider Info', this.renderProviderMeta(report.provider_meta), true)}
      <div class="section">
        <div class="section-title">Was this helpful?</div>
        <div class="section-content">
          <div class="rating">
            <button class="rating-btn ${evaluation?.rating === 'useful' ? 'selected useful' : ''}" data-rating="useful">👍 Useful</button>
            <button class="rating-btn ${evaluation?.rating === 'not_useful' ? 'selected not-useful' : ''}" data-rating="not_useful">👎 Not Useful</button>
          </div>
        </div>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" id="export-md">Export Markdown</button>
        <button class="btn btn-secondary" id="export-json">Export JSON</button>
      </div>
      <div class="inline-chat" id="inline-chat">
        <div class="chat-toggle" id="chat-toggle">
          <span>Chat</span>
          <span class="toggle-arrow">&#9660;</span>
        </div>
        <div class="chat-thread">
          <div class="chat-messages" id="chat-messages"></div>
          <div class="chat-input-bar">
            <input type="text" id="chat-input" placeholder="Ask about this report..." />
            <button id="chat-send" class="btn btn-primary" disabled>Send</button>
          </div>
        </div>
      </div>
    `;
    this.bindReportEvents(report);
    this.bindInlineChat();
    this.applyRtl(this.reportViewEl);
  }

  private bindReportEvents(report: IdeaReport): void {
    this.reportViewEl.querySelectorAll('.section-header').forEach((header) => {
      header.addEventListener('click', () => {
        header.parentElement?.classList.toggle('collapsed');
      });
    });

    this.reportViewEl.querySelectorAll('.rating-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const rating = btn.getAttribute('data-rating') as 'useful' | 'not_useful';
        await this.submitRating(report.id, rating);
        this.reportViewEl.querySelectorAll('.rating-btn').forEach((b) => b.classList.remove('selected', 'useful', 'not-useful'));
        btn.classList.add('selected', rating === 'useful' ? 'useful' : 'not-useful');
      });
    });

    document.getElementById('export-md')?.addEventListener('click', () => this.exportMarkdown(report));
    document.getElementById('export-json')?.addEventListener('click', () => this.exportJSON(report));
  }

  private async submitRating(ideaId: string, rating: 'useful' | 'not_useful'): Promise<void> {
    const evaluation: Evaluation = {
      idea_id: ideaId,
      rating,
      created_at: new Date().toISOString(),
    };
    await saveEvaluation(evaluation);
    this.evaluations.set(ideaId, evaluation);
  }

  private renderSection(title: string, content: string, collapsed = false): string {
    return `
      <div class="section${collapsed ? ' collapsed' : ''}">
        <div class="section-header">
          <span class="section-title">${title}</span>
          <span class="section-toggle">▼</span>
        </div>
        <div class="section-content">${content}</div>
      </div>
    `;
  }

  private renderExecutiveSummary(summary: string[]): string {
    return `<ul class="list">${summary.map((s) => `<li>${this.escapeHtml(s)}</li>`).join('')}</ul>`;
  }

  private renderRecommendationBadge(rec?: Recommendation | null): string {
    if (!rec) return '';
    const cls = rec.signal === 'BUY' ? 'rec-buy' : rec.signal === 'SELL' ? 'rec-sell' : 'rec-hold';
    return `<span class="rec-badge ${cls}" title="${this.escapeHtml(rec.rationale)}">${rec.signal} ${Math.round(rec.certainty * 100)}%</span>`;
  }

  private renderTickers(tickers: IdeaReport['tickers']): string {
    if (tickers.length === 0) return '<p>No tickers identified</p>';
    return `
      <div class="tickers">
        ${tickers
          .map(
            (t) => {
              const isUserProvided = t.confidence === 1.0;
              return `
          <span class="ticker${isUserProvided ? ' user-provided' : ''}">
            <span class="ticker-symbol">${this.escapeHtml(t.symbol)}</span>
            ${isUserProvided ? '<span class="ticker-user-label">(user)</span>' : `<span class="ticker-confidence">${Math.round(t.confidence * 100)}%</span>`}
            ${this.renderRecommendationBadge(t.recommendation)}
          </span>
        `;
            }
          )
          .join('')}
      </div>
    `;
  }

  private renderRelatedTickers(tickers: RelatedTicker[]): string {
    if (!tickers.length) return '<p>No related tickers discovered</p>';
    const grouped = new Map<string, RelatedTicker[]>();
    for (const t of tickers) {
      const list = grouped.get(t.primary_symbol) || [];
      list.push(t);
      grouped.set(t.primary_symbol, list);
    }
    let html = '';
    for (const [primary, related] of grouped) {
      html += `<div class="related-group"><div class="related-primary">Related to ${this.escapeHtml(primary)}</div>`;
      html += related.map((t) => `
        <div class="related-ticker">
          <div class="related-ticker-header">
            <span class="ticker-symbol">${this.escapeHtml(t.symbol)}</span>
            <span class="related-name">${this.escapeHtml(t.company_name)}</span>
            ${this.renderRecommendationBadge(t.recommendation)}
          </div>
          <div class="related-meta">
            <span class="relationship-badge">${t.relationship.replace('_', ' ')}</span>
            <span class="depth-label">Depth ${t.depth}</span>
          </div>
        </div>
      `).join('');
      html += '</div>';
    }
    return html;
  }

  private renderQuotes(quotes: IdeaReport['rationale_quotes']): string {
    if (quotes.length === 0) return '<p>No supporting quotes</p>';
    return quotes.map((q) => `<div class="quote">"${this.escapeHtml(q.quote)}"</div>`).join('');
  }

  private renderList(items: string[], className = ''): string {
    if (items.length === 0) return '<p>None identified</p>';
    return `<ul class="list ${className}">${items.map((item) => `<li>${this.escapeHtml(item)}</li>`).join('')}</ul>`;
  }

  private renderConfidence(report: IdeaReport): string {
    if (report.confidence_score == null) return '<p>No confidence score available</p>';
    const score = Math.round(report.confidence_score * 100);
    return `
      <div class="confidence-bar">
        <div class="confidence-track">
          <div class="confidence-fill" style="width: ${score}%"></div>
        </div>
        <div class="confidence-score">${score}%</div>
      </div>
      ${report.confidence_explanation ? `<div class="confidence-explanation">${this.escapeHtml(report.confidence_explanation)}</div>` : ''}
    `;
  }

  private renderQuantitativeData(data: QuantitativeEntry[]): string {
    if (!data.length) return '<p>No quantitative data available</p>';
    return data.map((entry) => {
      const f = entry.fundamentals;
      const t = entry.technicals;
      let html = `<div class="quantitative-card">
        <div class="quantitative-header"><strong>${this.escapeHtml(entry.ticker)}</strong> - ${this.escapeHtml(entry.company_name)}</div>
        <div class="quantitative-section"><strong>Fundamentals</strong><table class="metrics-table"><tbody>`;
      if (f.pe_ratio != null) html += `<tr><td>P/E Ratio</td><td>${f.pe_ratio.toFixed(2)}</td></tr>`;
      if (f.market_cap) html += `<tr><td>Market Cap</td><td>${this.escapeHtml(f.market_cap)}</td></tr>`;
      if (f.revenue) html += `<tr><td>Revenue</td><td>${this.escapeHtml(f.revenue)}</td></tr>`;
      if (f.eps != null) html += `<tr><td>EPS</td><td>${f.eps.toFixed(2)}</td></tr>`;
      if (f.profit_margin != null) html += `<tr><td>Profit Margin</td><td>${(f.profit_margin * 100).toFixed(1)}%</td></tr>`;
      if (f.dividend_yield != null) html += `<tr><td>Dividend Yield</td><td>${(f.dividend_yield * 100).toFixed(2)}%</td></tr>`;
      html += '</tbody></table></div>';
      if (t) {
        html += '<div class="quantitative-section"><strong>Technical Indicators</strong><table class="metrics-table"><tbody>';
        if (t.current_price != null) html += `<tr><td>Current Price</td><td>$${t.current_price.toFixed(2)}</td></tr>`;
        if (t.ma_50 != null) html += `<tr><td>50-Day MA</td><td>$${t.ma_50.toFixed(2)}</td></tr>`;
        if (t.ma_200 != null) html += `<tr><td>200-Day MA</td><td>$${t.ma_200.toFixed(2)}</td></tr>`;
        if (t.rsi_14 != null) {
          const rsiClass = t.rsi_14 > 70 ? 'rsi-overbought' : t.rsi_14 < 30 ? 'rsi-oversold' : '';
          const rsiLabel = t.rsi_14 > 70 ? ' (Overbought)' : t.rsi_14 < 30 ? ' (Oversold)' : '';
          html += `<tr><td>RSI (14)</td><td class="${rsiClass}">${t.rsi_14.toFixed(1)}${rsiLabel}</td></tr>`;
        }
        if (t.price_change_1w != null) html += `<tr><td>1-Week Change</td><td class="${t.price_change_1w >= 0 ? 'change-positive' : 'change-negative'}">${(t.price_change_1w * 100).toFixed(2)}%</td></tr>`;
        if (t.price_change_1m != null) html += `<tr><td>1-Month Change</td><td class="${t.price_change_1m >= 0 ? 'change-positive' : 'change-negative'}">${(t.price_change_1m * 100).toFixed(2)}%</td></tr>`;
        if (t.price_change_3m != null) html += `<tr><td>3-Month Change</td><td class="${t.price_change_3m >= 0 ? 'change-positive' : 'change-negative'}">${(t.price_change_3m * 100).toFixed(2)}%</td></tr>`;
        html += '</tbody></table></div>';
      }
      html += '</div>';
      return html;
    }).join('');
  }

  private renderProviderMeta(meta: IdeaReport['provider_meta']): string {
    return `
      <div class="provider-meta">
        Provider: ${meta.provider} | Model: ${meta.model} | Temperature: ${meta.temperature} | Duration: ${meta.pipeline_duration_ms}ms
      </div>
    `;
  }

  private renderDataSourceBadge(source: string): string {
    const label = source === 'web_search' ? 'Web Search' : 'LLM Knowledge';
    const cls = source === 'web_search' ? 'badge-web' : 'badge-llm';
    return `<span class="data-source-badge ${cls}">${label}</span>`;
  }

  private renderAgentLabel(sectionName: string, attributions?: Record<string, string[]> | null): string {
    if (!attributions) return '';
    const agents = attributions[sectionName];
    if (!agents?.length) return '';
    const labels: Record<string, string> = {
      news_agent: 'News Agent', fundamentals_agent: 'Fundamentals Agent',
      risk_agent: 'Risk Agent', macro_agent: 'Macro Agent', synthesis_agent: 'Synthesis Agent',
    };
    return `<div class="agent-attribution">${agents.map((a) => labels[a] || a).join(', ')}</div>`;
  }

  private renderSentimentBadge(sentiment: string): string {
    const cls = sentiment === 'positive' ? 'sentiment-positive' : sentiment === 'negative' ? 'sentiment-negative' : 'sentiment-neutral';
    return `<span class="sentiment-badge ${cls}">${sentiment}</span>`;
  }

  private renderNewsContext(items: NewsItem[], attributions?: Record<string, string[]> | null): string {
    return `
      ${this.renderAgentLabel('news_context', attributions)}
      ${items.map((item) => `
        <div class="news-item">
          <div class="news-headline">
            <a href="${this.escapeHtml(item.url)}" target="_blank">${this.escapeHtml(item.headline)}</a>
            ${this.renderSentimentBadge(item.sentiment)}
          </div>
          <div class="news-meta">
            ${this.escapeHtml(item.source)} • ${this.escapeHtml(item.published_date)}
            • Relevance: ${Math.round(item.relevance_score * 100)}%
            ${this.renderDataSourceBadge(item.data_source)}
          </div>
          <div class="news-summary">${this.escapeHtml(item.summary)}</div>
        </div>
      `).join('')}
    `;
  }

  private renderFundamentals(snapshots: FundamentalsSnapshot[], attributions?: Record<string, string[]> | null): string {
    return `
      ${this.renderAgentLabel('fundamentals_summary', attributions)}
      ${snapshots.map((snap) => `
        <div class="fundamentals-card">
          <div class="fundamentals-header">
            <strong>${this.escapeHtml(snap.ticker)}</strong> - ${this.escapeHtml(snap.company_name)}
            ${this.renderDataSourceBadge(snap.data_source)}
          </div>
          <table class="metrics-table">
            <thead><tr><th>Metric</th><th>Value</th><th>Period</th></tr></thead>
            <tbody>
              ${snap.metrics.map((m) => `
                <tr>
                  <td>${this.escapeHtml(m.name)}</td>
                  <td>${this.escapeHtml(m.value)}</td>
                  <td>${m.period ? this.escapeHtml(m.period) : '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `).join('')}
    `;
  }

  private renderCrossReference(analysis: IdeaReport['cross_reference_analysis']): string {
    if (!analysis) return '';
    return `
      ${analysis.convergences.length ? `
        <div class="xref-section">
          <strong>Convergences</strong>
          <ul class="list">${analysis.convergences.map((c) => `<li>${this.escapeHtml(c)}</li>`).join('')}</ul>
        </div>
      ` : ''}
      ${analysis.divergences.length ? `
        <div class="xref-section">
          <strong>Divergences</strong>
          ${analysis.divergences.map((d) => `
            <div class="divergence-card">
              <div class="divergence-topic">${this.escapeHtml(d.topic)}</div>
              <div class="divergence-findings">
                <div><strong>${this.escapeHtml(d.source_a)}:</strong> ${this.escapeHtml(d.finding_a)}</div>
                <div><strong>${this.escapeHtml(d.source_b)}:</strong> ${this.escapeHtml(d.finding_b)}</div>
              </div>
              <div class="divergence-explanation">${this.escapeHtml(d.explanation)}</div>
            </div>
          `).join('')}
        </div>
      ` : ''}
      ${analysis.deduplicated_risks.length ? `
        <div class="xref-section">
          <strong>Deduplicated Risks</strong>
          <ul class="list risks">${analysis.deduplicated_risks.map((r) => `<li>${this.escapeHtml(r)}</li>`).join('')}</ul>
        </div>
      ` : ''}
    `;
  }

  private renderMacroContext(macro: IdeaReport['macro_context']): string {
    if (!macro) return '';
    return `
      <div class="macro-section">
        <div><strong>Sector:</strong> ${this.escapeHtml(macro.sector)} ${this.renderDataSourceBadge(macro.data_source)}</div>
        ${macro.sector_trends.length ? `<div><strong>Trends:</strong><ul class="list">${macro.sector_trends.map((t) => `<li>${this.escapeHtml(t)}</li>`).join('')}</ul></div>` : ''}
        ${macro.economic_indicators.length ? `<div><strong>Indicators:</strong><ul class="list">${macro.economic_indicators.map((i) => `<li>${this.escapeHtml(i)}</li>`).join('')}</ul></div>` : ''}
        ${macro.headwinds.length ? `<div><strong>Headwinds:</strong><ul class="list risks">${macro.headwinds.map((h) => `<li>${this.escapeHtml(h)}</li>`).join('')}</ul></div>` : ''}
        ${macro.tailwinds.length ? `<div><strong>Tailwinds:</strong><ul class="list">${macro.tailwinds.map((t) => `<li>${this.escapeHtml(t)}</li>`).join('')}</ul></div>` : ''}
      </div>
    `;
  }

  private renderThinkingOutput(output: Record<string, { agent_id: string; phase: string; content: string }>): string {
    const entries = Object.values(output);
    const parallel = entries.filter((e) => e.phase === 'parallel');
    const sequential = entries.filter((e) => e.phase === 'sequential');
    let html = '<div class="thinking-section static">';
    if (parallel.length > 0) {
      html += '<div class="thinking-phase-group"><div class="thinking-phase-label">Parallel Analysis</div>';
      for (const entry of parallel) {
        const label = PanelController.AGENT_LABELS[entry.agent_id] || entry.agent_id;
        html += `<details class="thinking-agent"><summary>${this.escapeHtml(label)}</summary>`;
        html += `<pre class="thinking-content">${this.escapeHtml(entry.content.slice(0, PanelController.THINKING_MAX_CHARS))}</pre></details>`;
      }
      html += '</div>';
    }
    for (const entry of sequential) {
      const label = PanelController.AGENT_LABELS[entry.agent_id] || entry.agent_id;
      html += `<details class="thinking-agent"><summary>${this.escapeHtml(label)}</summary>`;
      html += `<pre class="thinking-content">${this.escapeHtml(entry.content.slice(0, PanelController.THINKING_MAX_CHARS))}</pre></details>`;
    }
    html += '</div>';
    return html;
  }

  private renderCommunicationLog(messages: AgentMessage[]): string {
    return `
      <div class="comm-log">
        ${messages.map((m) => `
          <div class="log-entry">
            <div class="log-meta">
              <strong>${this.escapeHtml(m.sender)}</strong> → ${this.escapeHtml(m.recipient)}
              <span class="log-type">${m.message_type}</span>
              <span class="log-round">R${m.round_number}</span>
            </div>
            <div class="log-content">${this.escapeHtml(JSON.stringify(m.content).slice(0, 200))}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  private exportMarkdown(report: IdeaReport): void {
    const md = generateMarkdown(report);
    const filename = `${report.tickers[0]?.symbol || 'report'}-${report.id.slice(0, 8)}.md`;
    downloadFile(filename, md, 'text/markdown');
  }

  private exportJSON(report: IdeaReport): void {
    const json = generateJSON(report);
    const filename = `${report.tickers[0]?.symbol || 'report'}-${report.id.slice(0, 8)}.json`;
    downloadFile(filename, json, 'application/json');
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  private truncateUrl(url: string): string {
    try {
      const parsed = new URL(url);
      return parsed.hostname + (parsed.pathname.length > 20 ? parsed.pathname.slice(0, 20) + '...' : parsed.pathname);
    } catch {
      return url.slice(0, 40) + '...';
    }
  }

  private formatDate(dateStr: string): string {
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  }
}

new PanelController();
