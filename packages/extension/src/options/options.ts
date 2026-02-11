import type { UserSettings } from '../types';
import { getSettings, saveSettings } from '../lib/storage';

const MODEL_HINTS: Record<string, string> = {
  openai: 'Recommended: gpt-4o, gpt-4-turbo, gpt-3.5-turbo',
  anthropic: 'Recommended: claude-3-5-sonnet-20241022, claude-3-opus-20240229',
  ollama: 'Recommended: llama3, mistral, mixtral',
};

const DEFAULT_MODELS: Record<string, string> = {
  openai: 'gpt-4o',
  anthropic: 'claude-3-5-sonnet-20241022',
  ollama: 'llama3',
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
  private saveBtn: HTMLButtonElement;
  private resetBtn: HTMLButtonElement;
  private toast: HTMLElement;

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
    this.saveBtn = document.getElementById('save-btn') as HTMLButtonElement;
    this.resetBtn = document.getElementById('reset-btn') as HTMLButtonElement;
    this.toast = document.getElementById('toast')!;
    this.bindEvents();
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
    }
  }

  private handleProviderChange(): void {
    const provider = this.providerSelect.value as UserSettings['provider'] | '';
    const isCloud = provider === 'openai' || provider === 'anthropic';
    const isOllama = provider === 'ollama';
    const needsBaseUrl = provider === 'openai' || provider === 'ollama';

    this.apiKeyGroup.classList.toggle('visible', isCloud);
    this.baseUrlGroup.classList.toggle('visible', needsBaseUrl);

    const baseUrlHint = document.getElementById('base-url-hint');
    if (baseUrlHint) {
      if (isOllama) {
        baseUrlHint.textContent = 'Required: URL where Ollama is running (e.g., http://localhost:11434)';
        this.baseUrlInput.placeholder = 'http://localhost:11434';
      } else if (provider === 'openai') {
        baseUrlHint.textContent = 'Optional: Custom OpenAI-compatible endpoint. Leave empty for official OpenAI API.';
        this.baseUrlInput.placeholder = 'https://api.openai.com/v1';
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
      web_lookup: false,
    };
    if (settings.provider === 'openai' || settings.provider === 'anthropic') {
      settings.api_key = this.apiKeyInput.value.trim() || undefined;
    }
    if (settings.provider === 'openai' || settings.provider === 'ollama') {
      const baseUrl = this.baseUrlInput.value.trim();
      if (baseUrl) {
        settings.base_url = baseUrl;
      }
    }
    await saveSettings(settings);
    this.showToast('Settings saved successfully');
  }

  private handleReset(): void {
    this.providerSelect.value = '';
    this.apiKeyInput.value = '';
    this.baseUrlInput.value = 'http://localhost:11434';
    this.modelInput.value = '';
    this.temperatureInput.value = '0.7';
    this.temperatureValue.textContent = '0.7';
    this.piiRedactionInput.checked = true;
    this.handleProviderChange();
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
