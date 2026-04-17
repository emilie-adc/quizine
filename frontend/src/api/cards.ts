export interface CardResponse {
  id: number
  deck_id: number
  type: string
  front: string | null
  back: string | null
  custom_topic_tag: string | null
  approved: boolean
  created_at: string
}

export interface CardUpdate {
  front?: string
  back?: string
  custom_topic_tag?: string
}

export async function updateCard(id: number, body: CardUpdate): Promise<CardResponse> {
  const resp = await fetch(`/api/cards/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) throw new Error('Failed to update card')
  return resp.json()
}

export async function deleteCard(id: number): Promise<void> {
  const resp = await fetch(`/api/cards/${id}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('Failed to delete card')
}

export async function approveCard(id: number): Promise<CardResponse> {
  const resp = await fetch(`/api/cards/${id}/approve`, { method: 'POST' })
  if (!resp.ok) throw new Error('Failed to approve card')
  return resp.json()
}
