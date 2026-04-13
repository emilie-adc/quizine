// Types -------------------------------------------------------------------

export interface MCQRequest {
  text: string
  certification?: string
  n_questions?: number
  stream?: boolean
}

export interface MCQQuestion {
  question: string
  options: [string, string, string, string]
  correct_index: 0 | 1 | 2 | 3
  topic_tag: string
}

export interface FlashcardRequest {
  text: string
  certification?: string
  n_cards?: number
  topic_tags?: string[]
  stream?: boolean
}

export interface Flashcard {
  front: string
  back: string
  topic_tag: string
}

// SSE helpers -------------------------------------------------------------

/**
 * Read an SSE response body, accumulating delta chunks.
 * Calls onDelta with each chunk as it arrives.
 * Resolves with the full accumulated JSON string when [DONE] is received.
 */
async function readSSEStream(
  response: Response,
  onDelta: (delta: string) => void,
): Promise<string> {
  if (!response.body) throw new Error('Response has no body')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let accumulated = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const payload = line.slice('data: '.length)
      if (payload === '[DONE]') return accumulated
      const { delta } = JSON.parse(payload) as { delta: string }
      accumulated += delta
      onDelta(delta)
    }
  }

  buffer += decoder.decode()
  const remainingLines = buffer.split('\n')

  for (const line of remainingLines) {
    if (!line.startsWith('data: ')) continue
    const payload = line.slice('data: '.length)
    if (payload === '[DONE]') return accumulated
    const { delta } = JSON.parse(payload) as { delta: string }
    accumulated += delta
    onDelta(delta)
  }
  return accumulated
}

// Public API --------------------------------------------------------------

export async function streamMCQ(
  req: MCQRequest,
  onDelta: (delta: string) => void,
): Promise<MCQQuestion[]> {
  const response = await fetch('/api/generate/mcq', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...req, stream: true }),
  })

  if (!response.ok) throw new Error(`Generate MCQ failed: ${response.status}`)

  const json = await readSSEStream(response, onDelta)
  return JSON.parse(json) as MCQQuestion[]
}

export async function streamFlashcards(
  req: FlashcardRequest,
  onDelta: (delta: string) => void,
): Promise<Flashcard[]> {
  const response = await fetch('/api/generate/flashcards', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...req, stream: true }),
  })

  if (!response.ok) throw new Error(`Generate flashcards failed: ${response.status}`)

  const json = await readSSEStream(response, onDelta)
  return JSON.parse(json) as Flashcard[]
}
