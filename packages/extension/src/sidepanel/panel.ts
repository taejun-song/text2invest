import type { AgentResult, ChatMessage, Evaluation, GenerationState, IdeaReport, NewsItem, FundamentalsSnapshot, AgentMessage, ThinkingChunk } from '../types';
import { getReports, getEvaluations, getSettings, searchReports, saveEvaluation } from '../lib/storage';
import { chatWithReport } from '../lib/api';
import { generateMarkdown, generateJSON, downloadFile } from '../lib/export';

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
  }

  private async init(): Promise<void> {
    const evals = await getEvaluations();
    evals.forEach((e) => this.evaluations.set(e.idea_id, e));
    const state = await this.getState();
    if (state.status === 'completed' && state.report) {
      this.currentReport = state.report;
      this.renderReport(state.report);
      this.showTab('report');
    } else if (state.status === 'generating') {
      this.renderProgress(state);
      this.startPolling();
    } else {
      await this.loadHistory();
    }
  }

  private static readonly STAGE_LABELS: Record<string, string> = {
    extraction: 'Extracting text',
    entity: 'Identifying entities',
    ticker: 'Mapping tickers',
    thesis: 'Generating thesis',
    critique: 'Analyzing risks',
    confidence: 'Scoring confidence',
    enrichment: 'Data agents',
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
    'extraction', 'entity', 'ticker', 'thesis', 'critique', 'confidence', 'enrichment', 'formatting',
  ];

  private renderProgress(state: GenerationState): void {
    this.emptyStateEl.classList.add('hidden');
    this.historyViewEl.classList.add('hidden');
    this.reportViewEl.classList.remove('hidden');

    const completed = state.completed_stages || [];
    const enrichmentAgents = state.enrichment_agents || [];
    const currentStage = state.current_stage || '';
    const results = state.agent_results || [];

    const stagesHtml = PanelController.PIPELINE_STAGES.map((stage) => {
      const isDone = completed.includes(stage) && (stage !== 'enrichment' || completed.includes('formatting'));
      const isCurrent = !isDone && completed.includes(stage) || currentStage === stage;
      const icon = isDone ? '<span class="stage-icon done">&#10003;</span>'
        : isCurrent ? '<span class="stage-icon current"><span class="spinner-sm"></span></span>'
        : '<span class="stage-icon pending">&#9675;</span>';
      const label = PanelController.STAGE_LABELS[stage] || stage;
      const cls = isDone ? 'done' : isCurrent ? 'current' : 'pending';
      const resultPreview = this.renderResultPreview(stage, results);

      let agentSublist = '';
      if (stage === 'enrichment' && enrichmentAgents.length > 0) {
        agentSublist = '<ul class="agent-progress">' + enrichmentAgents.map((agentId) => {
          const agentDone = completed.includes(`agent:${agentId}`);
          const agentActive = !agentDone && completed.includes('enrichment');
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
    const stageLabel = PanelController.STAGE_LABELS[currentStage] || currentStage || 'Starting';

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
    this.showTab('report');
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
    let text = '';
    if (agentId === 'entity') {
      const companies = s.companies as string[] | undefined;
      text = companies?.length ? companies.join(', ') : '';
    } else if (agentId === 'ticker') {
      const tickers = s.tickers as Array<{ symbol: string; confidence: number }> | undefined;
      text = tickers?.map((t) => `${t.symbol} (${Math.round(t.confidence * 100)}%)`).join(', ') || '';
    } else if (agentId === 'thesis') {
      text = (s.thesis as string || '').slice(0, 120) + ((s.thesis as string || '').length > 120 ? '...' : '');
    } else if (agentId === 'critique') {
      const risks = s.risks as string[] | undefined;
      text = risks?.length ? `${s.risks_count} risks: ${risks[0].slice(0, 60)}...` : '';
    } else if (agentId === 'confidence') {
      text = `Score: ${Math.round((s.score as number || 0) * 100)}%`;
    } else if (agentId === 'news_agent') {
      const headlines = s.headlines as string[] | undefined;
      text = headlines?.length ? `${s.count} articles — ${headlines[0]}` : `${s.count || 0} articles`;
    } else if (agentId === 'fundamentals_agent') {
      const metrics = s.metrics as Array<{ name: string; value: string }> | undefined;
      text = metrics?.map((m) => `${m.name}: ${m.value}`).join(' · ') || '';
    } else if (agentId === 'macro_agent') {
      text = `${s.sector || ''}`;
      if (s.tailwinds || s.headwinds) text += ` — ${s.tailwinds} tailwinds, ${s.headwinds} headwinds`;
    } else if (agentId === 'risk_agent') {
      text = s.top_risk ? `${s.risks_count} risks — ${(s.top_risk as string).slice(0, 80)}` : '';
    }
    if (!text) return '';
    return `<div class="result-preview">${this.escapeHtml(text)}</div>`;
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
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: 'GET_STATE' }, (response: GenerationState) => {
        resolve(response || { status: 'idle' });
      });
    });
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
        ⚠️ Educational only - Not financial advice
      </div>
      ${this.renderSection('Executive Summary', this.renderExecutiveSummary(report.executive_summary))}
      ${this.renderSection('Tickers', this.renderTickers(report.tickers))}
      ${this.renderSection('Investment Thesis', `<div class="thesis">${this.escapeHtml(report.thesis)}</div>`)}
      ${this.renderSection('Supporting Quotes', this.renderQuotes(report.rationale_quotes))}
      ${this.renderSection('Catalysts', this.renderList(report.catalysts))}
      ${this.renderSection('Risks', this.renderList(report.risks, 'risks'))}
      ${this.renderSection('Counter-Thesis', `<div class="counter-thesis">${this.escapeHtml(report.counter_thesis)}</div>`)}
      ${this.renderSection('Confidence', this.renderConfidence(report))}
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

  private renderTickers(tickers: IdeaReport['tickers']): string {
    if (tickers.length === 0) return '<p>No tickers identified</p>';
    return `
      <div class="tickers">
        ${tickers
          .map(
            (t) => `
          <span class="ticker">
            <span class="ticker-symbol">${this.escapeHtml(t.symbol)}</span>
            <span class="ticker-confidence">${Math.round(t.confidence * 100)}%</span>
          </span>
        `
          )
          .join('')}
      </div>
    `;
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
    const score = Math.round(report.confidence_score * 100);
    return `
      <div class="confidence-bar">
        <div class="confidence-track">
          <div class="confidence-fill" style="width: ${score}%"></div>
        </div>
        <div class="confidence-score">${score}%</div>
      </div>
      <div class="confidence-explanation">${this.escapeHtml(report.confidence_explanation)}</div>
    `;
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
