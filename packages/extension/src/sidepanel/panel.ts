import type { Evaluation, GenerationState, IdeaReport, NewsItem, FundamentalsSnapshot, AgentMessage } from '../types';
import { getReports, getEvaluations, searchReports, saveEvaluation } from '../lib/storage';
import { generateMarkdown, generateJSON, downloadFile } from '../lib/export';

class PanelController {
  private contentEl: HTMLElement;
  private emptyStateEl: HTMLElement;
  private reportViewEl: HTMLElement;
  private historyViewEl: HTMLElement;
  private tabReportBtn: HTMLButtonElement;
  private tabHistoryBtn: HTMLButtonElement;
  private currentReport: IdeaReport | null = null;
  private evaluations: Map<string, Evaluation> = new Map();

  constructor() {
    this.contentEl = document.getElementById('content')!;
    this.emptyStateEl = document.getElementById('empty-state')!;
    this.reportViewEl = document.getElementById('report-view')!;
    this.historyViewEl = document.getElementById('history-view')!;
    this.tabReportBtn = document.getElementById('tab-report') as HTMLButtonElement;
    this.tabHistoryBtn = document.getElementById('tab-history') as HTMLButtonElement;
    this.bindEvents();
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
    } else {
      await this.loadHistory();
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

    if (tab === 'report') {
      this.historyViewEl.classList.add('hidden');
      if (this.currentReport) {
        this.emptyStateEl.classList.add('hidden');
        this.reportViewEl.classList.remove('hidden');
      } else {
        this.emptyStateEl.classList.remove('hidden');
        this.reportViewEl.classList.add('hidden');
      }
    } else {
      this.emptyStateEl.classList.add('hidden');
      this.reportViewEl.classList.add('hidden');
      this.historyViewEl.classList.remove('hidden');
      this.loadHistory();
    }
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
    `;
    this.bindReportEvents(report);
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
