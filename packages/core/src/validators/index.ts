import ideaReportSchema from '../schemas/idea-report.json';
import tickerSchema from '../schemas/ticker.json';
import rationaleQuoteSchema from '../schemas/rationale-quote.json';
import sourceSchema from '../schemas/source.json';
import providerMetaSchema from '../schemas/provider-meta.json';
import userSettingsSchema from '../schemas/user-settings.json';
import evaluationSchema from '../schemas/evaluation.json';

export const schemas = {
  ideaReport: ideaReportSchema,
  ticker: tickerSchema,
  rationaleQuote: rationaleQuoteSchema,
  source: sourceSchema,
  providerMeta: providerMetaSchema,
  userSettings: userSettingsSchema,
  evaluation: evaluationSchema,
} as const;

export type SchemaName = keyof typeof schemas;

export function validateRequired<T>(obj: unknown, schemaName: SchemaName): T {
  const schema = schemas[schemaName];
  if (!schema || typeof obj !== 'object' || obj === null) {
    throw new Error(`Invalid object for schema: ${schemaName}`);
  }
  const required = (schema as { required?: string[] }).required || [];
  for (const field of required) {
    if (!(field in obj)) {
      throw new Error(`Missing required field "${field}" in ${schemaName}`);
    }
  }
  return obj as T;
}

export function isValidConfidence(value: unknown): value is number {
  return typeof value === 'number' && value >= 0 && value <= 1;
}

export function isValidHorizon(value: unknown): value is 'short' | 'medium' | 'long' {
  return value === 'short' || value === 'medium' || value === 'long';
}

export function isValidProvider(value: unknown): value is 'openai' | 'anthropic' | 'ollama' {
  return value === 'openai' || value === 'anthropic' || value === 'ollama';
}

export function isValidRating(value: unknown): value is 'useful' | 'not_useful' {
  return value === 'useful' || value === 'not_useful';
}

export function isValidTickerSymbol(value: unknown): boolean {
  return typeof value === 'string' && /^[A-Z]{1,5}$/.test(value);
}
