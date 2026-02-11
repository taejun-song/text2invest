import type { Evaluation, GenerationState, IdeaReport } from '../types';
import { getReports, getEvaluations, searchReports, saveEvaluation } from '../lib/storage';

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

  private exportMarkdown(report: IdeaReport): void {
    const md = this.generateMarkdown(report);
    this.downloadFile(`${report.tickers[0]?.symbol || 'report'}-${report.id.slice(0, 8)}.md`, md, 'text/markdown');
  }

  private exportJSON(report: IdeaReport): void {
    const json = JSON.stringify(report, null, 2);
    this.downloadFile(`${report.tickers[0]?.symbol || 'report'}-${report.id.slice(0, 8)}.json`, json, 'application/json');
  }

  private generateMarkdown(report: IdeaReport): string {
    return `# Investment Analysis: ${report.source.title || 'Untitled'}

> ⚠️ **Disclaimer**: Educational only - Not financial advice

**Source**: [${report.source.url}](${report.source.url})
**Generated**: ${this.formatDate(report.created_at)}

## Executive Summary

${report.executive_summary.map((s) => `- ${s}`).join('\n')}

## Tickers

${report.tickers.map((t) => `- **${t.symbol}** (${t.company_name}) - Confidence: ${Math.round(t.confidence * 100)}%`).join('\n') || 'No tickers identified'}

## Investment Thesis

${report.thesis}

## Supporting Quotes

${report.rationale_quotes.map((q) => `> "${q.quote}"`).join('\n\n') || 'No supporting quotes'}

## Catalysts

${report.catalysts.map((c) => `- ${c}`).join('\n') || 'None identified'}

## Risks

${report.risks.map((r) => `- ⚠️ ${r}`).join('\n') || 'None identified'}

## Counter-Thesis

${report.counter_thesis}

## Confidence

**Score**: ${Math.round(report.confidence_score * 100)}%

${report.confidence_explanation}

## Time Horizon

${report.horizon}

## Limitations

${report.limitations.map((l) => `- ${l}`).join('\n') || 'None identified'}

---

*Generated by Text2Invest using ${report.provider_meta.provider}/${report.provider_meta.model}*
`;
  }

  private downloadFile(filename: string, content: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
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
