export interface DeckSummary {
  id: number
  title: string
  cert_id: number | null
  custom_cert_name: string | null
  created_at: string
}

export interface DeckDetail extends DeckSummary {
  cert_slug: string | null
  cert_display_name: string | null
  card_count: number
}

export interface DeckCreate {
  title: string
  cert_id?: number
  custom_cert_name?: string
}

export async function listDecks(): Promise<DeckSummary[]> {
  const resp = await fetch('/api/decks')
  if (!resp.ok) throw new Error('Failed to fetch decks')
  return resp.json()
}

export async function getDeck(id: number): Promise<DeckDetail> {
  const resp = await fetch(`/api/decks/${id}`)
  if (!resp.ok) throw new Error('Failed to fetch deck')
  return resp.json()
}

export async function createDeck(body: DeckCreate): Promise<DeckSummary> {
  const resp = await fetch('/api/decks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) throw new Error('Failed to create deck')
  return resp.json()
}
