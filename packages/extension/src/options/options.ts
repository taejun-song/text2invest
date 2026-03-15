import type { UserSettings, AgentConfig } from '../types';
import { getSettings, saveSettings } from '../lib/storage';

const MODEL_HINTS: Record<string, string> = {
  openai: 'Recommended: gpt-4o, gpt-4-turbo, gpt-3.5-turbo',
  anthropic: 'Recommended: claude-3-5-sonnet-20241022, claude-3-opus-20240229',
  ollama: 'Recommended: llama3, mistral, mixtral',
  nrp: 'Recommended: qwen3',
};

const DEFAULT_MODELS: Record<string, string> = {
  openai: 'gpt-4o',
  anthropic: 'claude-3-5-sonnet-20241022',
  ollama: 'llama3',
  nrp: 'qwen3',
};

const DEFAULT_AGENT_CONFIGS: AgentConfig[] = [
  { agent_id: 'news_agent', enabled: true, use_external_data: true },
  { agent_id: 'fundamentals_agent', enabled: true, use_external_data: true },
  { agent_id: 'risk_agent', enabled: true, use_external_data: true },
  { agent_id: 'macro_agent', enabled: false, use_external_data: true },
];

const AGENT_LABELS: Record<string, string> = {
  news_agent: 'News Agent',
  fundamentals_agent: 'Fundamentals Agent',
  risk_agent: 'Risk Agent',
  macro_agent: 'Macro Agent',
};

const AGENT_DESCRIPTIONS: Record<string, string> = {
  news_agent: 'Searches for recent news about identified companies',
  fundamentals_agent: 'Retrieves financial metrics for public companies',
  risk_agent: 'Cross-references findings from other agents to identify risks',
  macro_agent: 'Adds macro-economic context (sector trends, indicators)',
};

class OptionsController {
  private form: HTMLFormElement;
  private providerSelect: HTMLSelectElement;
  private apiKeyGroup: HTMLElement;
  private apiKeyInput: HTMLInputElement;
  private baseUrlGroup: HTMLElement;
  private baseUrlInput: HTMLInputElement;
  private modelInput: HTMLInputElement;
  private modelHint: HTMLElement;
  private temperatureInput: HTMLInputElement;
  private temperatureValue: HTMLElement;
  private piiRedactionInput: HTMLInputElement;
  private thinkingModeInput: HTMLInputElement;
  private outputLanguageSelect: HTMLSelectElement;
  private saveBtn: HTMLButtonElement;
  private resetBtn: HTMLButtonElement;
  private toast: HTMLElement;
  private agentConfigs: AgentConfig[] = [...DEFAULT_AGENT_CONFIGS];

  constructor() {
    this.form = document.getElementById('settings-form') as HTMLFormElement;
    this.providerSelect = document.getElementById('provider') as HTMLSelectElement;
    this.apiKeyGroup = document.getElementById('api-key-group')!;
    this.apiKeyInput = document.getElementById('api-key') as HTMLInputElement;
    this.baseUrlGroup = document.getElementById('base-url-group')!;
    this.baseUrlInput = document.getElementById('base-url') as HTMLInputElement;
    this.modelInput = document.getElementById('model') as HTMLInputElement;
    this.modelHint = document.getElementById('model-hint')!;
    this.temperatureInput = document.getElementById('temperature') as HTMLInputElement;
    this.temperatureValue = document.getElementById('temperature-value')!;
    this.piiRedactionInput = document.getElementById('pii-redaction') as HTMLInputElement;
    this.thinkingModeInput = document.getElementById('thinking-mode') as HTMLInputElement;
    this.outputLanguageSelect = document.getElementById('output-language') as HTMLSelectElement;
    this.saveBtn = document.getElementById('save-btn') as HTMLButtonElement;
    this.resetBtn = document.getElementById('reset-btn') as HTMLButtonElement;
    this.toast = document.getElementById('toast')!;
    this.bindEvents();
    this.renderAgentConfigs();
    this.loadSettings();
  }

  private bindEvents(): void {
    this.providerSelect.addEventListener('change', () => this.handleProviderChange());
    this.temperatureInput.addEventListener('input', () => {
      this.temperatureValue.textContent = this.temperatureInput.value;
    });
    this.form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSave();
    });
    this.resetBtn.addEventListener('click', () => this.handleReset());
  }

  private async loadSettings(): Promise<void> {
    const settings = await getSettings();
    if (settings) {
      this.providerSelect.value = settings.provider;
      this.handleProviderChange();
      this.apiKeyInput.value = settings.api_key || '';
      this.baseUrlInput.value = settings.base_url || 'http://localhost:11434';
      this.modelInput.value = settings.model;
      this.temperatureInput.value = String(settings.temperature);
      this.temperatureValue.textContent = String(settings.temperature);
      this.piiRedactionInput.checked = settings.pii_redaction;
      this.thinkingModeInput.checked = settings.thinking_mode ?? false;
      this.outputLanguageSelect.value = settings.output_language || 'en';
      if (settings.agent_configs?.length) {
        this.agentConfigs = settings.agent_configs;
        this.renderAgentConfigs();
      }
    }
  }

  private handleProviderChange(): void {
    const provider = this.providerSelect.value as UserSettings['provider'] | '';
    const isCloud = provider === 'openai' || provider === 'anthropic' || provider === 'nrp';
    const needsBaseUrl = provider === 'openai' || provider === 'ollama' || provider === 'nrp';

    this.apiKeyGroup.classList.toggle('visible', isCloud);
    this.baseUrlGroup.classList.toggle('visible', needsBaseUrl);

    const baseUrlHint = document.getElementById('base-url-hint');
    if (baseUrlHint) {
      if (provider === 'ollama') {
        baseUrlHint.textContent = 'Required: URL where Ollama is running (e.g., http://localhost:11434)';
        this.baseUrlInput.placeholder = 'http://localhost:11434';
      } else if (provider === 'openai') {
        baseUrlHint.textContent = 'Optional: Custom OpenAI-compatible endpoint. Leave empty for official OpenAI API.';
        this.baseUrlInput.placeholder = 'https://api.openai.com/v1';
      } else if (provider === 'nrp') {
        baseUrlHint.textContent = 'NRP.ai endpoint URL';
        this.baseUrlInput.placeholder = 'https://ellm.nrp-nautilus.io/v1';
        if (!this.baseUrlInput.value || this.baseUrlInput.value === 'http://localhost:11434') {
          this.baseUrlInput.value = 'https://ellm.nrp-nautilus.io/v1';
        }
      }
    }

    if (provider && MODEL_HINTS[provider]) {
      this.modelHint.textContent = MODEL_HINTS[provider];
      if (!this.modelInput.value) {
        this.modelInput.value = DEFAULT_MODELS[provider] || '';
      }
    } else {
      this.modelHint.textContent = '';
    }
  }

  private renderAgentConfigs(): void {
    const container = document.getElementById('agent-configs');
    if (!container) return;

    container.innerHTML = this.agentConfigs.map((cfg) => `
      <div class="agent-config-item" data-agent="${cfg.agent_id}">
        <div class="toggle-group">
          <div class="toggle-label">
            <span>${AGENT_LABELS[cfg.agent_id] || cfg.agent_id}</span>
            <small>${AGENT_DESCRIPTIONS[cfg.agent_id] || ''}</small>
          </div>
          <label class="toggle">
            <input type="checkbox" class="agent-enabled" ${cfg.enabled ? 'checked' : ''} />
            <span class="toggle-slider"></span>
          </label>
        </div>
        <div class="agent-sub-toggle ${cfg.enabled ? '' : 'disabled'}">
          <div class="toggle-group" style="padding-left: 16px;">
            <div class="toggle-label">
              <small>Use web search</small>
            </div>
            <label class="toggle">
              <input type="checkbox" class="agent-external-data" ${cfg.use_external_data ? 'checked' : ''} ${cfg.enabled ? '' : 'disabled'} />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>
    `).join('');

    container.querySelectorAll('.agent-config-item').forEach((item) => {
      const agentId = item.getAttribute('data-agent')!;
      const enabledInput = item.querySelector('.agent-enabled') as HTMLInputElement;
      const externalInput = item.querySelector('.agent-external-data') as HTMLInputElement;
      const subToggle = item.querySelector('.agent-sub-toggle') as HTMLElement;

      enabledInput.addEventListener('change', () => {
        const cfg = this.agentConfigs.find((c) => c.agent_id === agentId);
        if (cfg) cfg.enabled = enabledInput.checked;
        externalInput.disabled = !enabledInput.checked;
        subToggle.classList.toggle('disabled', !enabledInput.checked);
      });
      externalInput.addEventListener('change', () => {
        const cfg = this.agentConfigs.find((c) => c.agent_id === agentId);
        if (cfg) cfg.use_external_data = externalInput.checked;
      });
    });
  }

  private validate(): string | null {
    const provider = this.providerSelect.value;
    if (!provider) {
      return 'Please select a provider';
    }
    const hasApiKey = this.apiKeyInput.value.trim();
    const hasBaseUrl = this.baseUrlInput.value.trim();
    if (provider === 'openai' && !hasApiKey && !hasBaseUrl) {
      return 'API key or custom base URL is required for OpenAI';
    }
    if (provider === 'anthropic' && !hasApiKey) {
      return 'API key is required for Anthropic';
    }
    if (provider === 'ollama' && !hasBaseUrl) {
      return 'Base URL is required for Ollama';
    }
    if (provider === 'nrp' && !hasApiKey) {
      return 'API key is required for NRP.ai';
    }
    if (!this.modelInput.value.trim()) {
      return 'Model name is required';
    }
    return null;
  }

  private async handleSave(): Promise<void> {
    const error = this.validate();
    if (error) {
      this.showToast(error, true);
      return;
    }
    const settings: UserSettings = {
      provider: this.providerSelect.value as UserSettings['provider'],
      model: this.modelInput.value.trim(),
      temperature: parseFloat(this.temperatureInput.value),
      pii_redaction: this.piiRedactionInput.checked,
      thinking_mode: this.thinkingModeInput.checked,
      output_language: this.outputLanguageSelect.value,
      web_lookup: false,
      agent_configs: this.agentConfigs,
    };
    const provider = settings.provider;
    if (provider === 'openai' || provider === 'anthropic' || provider === 'nrp') {
      settings.api_key = this.apiKeyInput.value.trim() || undefined;
    }
    if (provider === 'openai' || provider === 'ollama' || provider === 'nrp') {
      const baseUrl = this.baseUrlInput.value.trim();
      if (baseUrl) {
        settings.base_url = baseUrl;
      }
    }
    settings.web_lookup = this.agentConfigs.some((c) => c.enabled && c.use_external_data);
    await saveSettings(settings);
    this.showToast('Settings saved successfully');
  }

  private handleReset(): void {
    this.providerSelect.value = import.meta.env.VITE_DEFAULT_PROVIDER || 'nrp';
    this.apiKeyInput.value = import.meta.env.VITE_DEFAULT_API_KEY || '';
    this.baseUrlInput.value = import.meta.env.VITE_DEFAULT_BASE_URL || 'https://ellm.nrp-nautilus.io/v1';
    this.modelInput.value = import.meta.env.VITE_DEFAULT_MODEL || 'qwen3';
    this.temperatureInput.value = '0.7';
    this.temperatureValue.textContent = '0.7';
    this.piiRedactionInput.checked = true;
    this.thinkingModeInput.checked = false;
    this.outputLanguageSelect.value = 'en';
    this.agentConfigs = [...DEFAULT_AGENT_CONFIGS];
    this.handleProviderChange();
    this.renderAgentConfigs();
    this.showToast('Settings reset to defaults');
  }

  private showToast(message: string, isError = false): void {
    this.toast.textContent = message;
    this.toast.classList.toggle('error', isError);
    this.toast.classList.add('visible');
    setTimeout(() => {
      this.toast.classList.remove('visible');
    }, 3000);
  }
}

new OptionsController();
