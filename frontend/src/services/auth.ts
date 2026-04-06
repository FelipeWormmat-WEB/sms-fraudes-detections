let apiKeyMemoryStore = "";

export function getApiKey(): string {
  return apiKeyMemoryStore;
}

export function setApiKey(value: string): void {
  apiKeyMemoryStore = value.trim();
}

export function clearApiKey(): void {
  apiKeyMemoryStore = "";
}
