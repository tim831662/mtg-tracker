// Matches docs/api-contract.md. Keep the backend's pagination and filters.
export async function getDecks({ format = '', offset = 0, signal } = {}) {
  const params = new URLSearchParams({ limit: '20', offset: String(offset) });
  if (format) params.set('format', format);
  const response = await fetch(`/api/decks?${params}`, { signal });
  if (!response.ok) throw new Error(`Deck API returned HTTP ${response.status}.`);
  const data = await response.json();
  if (!Array.isArray(data.items) || !Number.isInteger(data.total)) {
    throw new Error('Deck API returned an unexpected response.');
  }
  return data;
}
