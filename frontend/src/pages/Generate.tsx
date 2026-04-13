import { useEffect, useState } from 'react'
import { listCertifications, type CertificationSummary } from '../api/certifications'
import { streamFlashcards, streamMCQ, type Flashcard, type MCQQuestion } from '../api/generate'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type Mode = 'flashcard' | 'mcq'
type Card = Flashcard | MCQQuestion

/**
 * Extract complete JSON objects from a partial JSON array string, starting at
 * `startIndex` so only newly arrived content is scanned on each SSE delta.
 * Returns the parsed objects and the index after the last consumed character,
 * which should be passed as `startIndex` on the next call.
 */
function parsePartialCards<T>(
  partial: string,
  startIndex: number = 0,
): { cards: T[]; nextIndex: number } {
  const cards: T[] = []
  let depth = 0
  let start = -1
  let nextIndex = startIndex

  for (let i = startIndex; i < partial.length; i++) {
    const ch = partial[i]
    if (ch === '{') {
      if (depth === 0) start = i
      depth++
    } else if (ch === '}') {
      depth--
      if (depth === 0 && start !== -1) {
        try {
          cards.push(JSON.parse(partial.slice(start, i + 1)) as T)
          nextIndex = i + 1
        } catch {
          // Incomplete object — skip
        }
        start = -1
      }
    }
  }

  return { cards, nextIndex }
}

function isFlashcard(card: Card): card is Flashcard {
  return 'front' in card
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FlashcardView({ card }: { card: Flashcard }) {
  const [flipped, setFlipped] = useState(false)
  return (
    <button
      onClick={() => setFlipped(f => !f)}
      className="w-full text-left rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
    >
      <p className="text-xs font-medium text-indigo-500 uppercase tracking-wide mb-2">
        {card.topic_tag}
      </p>
      {flipped ? (
        <p className="text-gray-700">{card.back}</p>
      ) : (
        <p className="font-medium text-gray-900">{card.front}</p>
      )}
      <p className="text-xs text-gray-400 mt-3">{flipped ? 'Back — click to flip' : 'Front — click to flip'}</p>
    </button>
  )
}

function MCQView({ card }: { card: MCQQuestion }) {
  const [selected, setSelected] = useState<number | null>(null)
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium text-indigo-500 uppercase tracking-wide mb-2">
        {card.topic_tag}
      </p>
      <p className="font-medium text-gray-900 mb-4">{card.question}</p>
      <ul className="space-y-2">
        {card.options.map((opt, i) => {
          const isCorrect = i === card.correct_index
          const isSelected = i === selected
          let cls = 'w-full text-left rounded-lg border px-4 py-2 text-sm transition-colors '
          if (selected === null) {
            cls += 'border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
          } else if (isCorrect) {
            cls += 'border-green-400 bg-green-50 text-green-800'
          } else if (isSelected) {
            cls += 'border-red-300 bg-red-50 text-red-700'
          } else {
            cls += 'border-gray-100 text-gray-400'
          }
          return (
            <li key={i}>
              <button className={cls} onClick={() => setSelected(i)} disabled={selected !== null}>
                {opt}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Generate() {
  const [certs, setCerts] = useState<CertificationSummary[]>([])
  const [certSlug, setCertSlug] = useState<string>('custom')
  const [customCertName, setCustomCertName] = useState('')
  const [text, setText] = useState('')
  const [mode, setMode] = useState<Mode>('flashcard')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cards, setCards] = useState<Card[]>([])

  useEffect(() => {
    listCertifications()
      .then(setCerts)
      .catch(() => {/* backend not up yet — cert list stays empty */})
  }, [])

  const certContext =
    certSlug === 'custom'
      ? customCertName || undefined
      : certs.find(c => c.slug === certSlug)?.display_name

  async function handleGenerate() {
    if (!text.trim()) return
    setGenerating(true)
    setError(null)
    setCards([])

    // Capture mode so a mid-stream toggle doesn't corrupt parsing.
    const modeAtStart = mode
    let accumulated = ''
    let parsedUpTo = 0

    const onDelta = (delta: string) => {
      accumulated += delta
      if (modeAtStart === 'flashcard') {
        const { cards: newCards, nextIndex } = parsePartialCards<Flashcard>(accumulated, parsedUpTo)
        if (newCards.length > 0) {
          parsedUpTo = nextIndex
          setCards(prev => [...prev, ...newCards])
        }
      } else {
        const { cards: newCards, nextIndex } = parsePartialCards<MCQQuestion>(accumulated, parsedUpTo)
        if (newCards.length > 0) {
          parsedUpTo = nextIndex
          setCards(prev => [...prev, ...newCards])
        }
      }
    }

    try {
      if (modeAtStart === 'flashcard') {
        await streamFlashcards({ text, certification: certContext }, onDelta)
      } else {
        await streamMCQ({ text, certification: certContext }, onDelta)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-semibold text-gray-900 mb-1">Quizine</h1>
        <p className="text-gray-500 mb-8">Knowledge, served fresh.</p>

        {/* Cert picker */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Certification</label>
          <select
            value={certSlug}
            onChange={e => setCertSlug(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {certs.map(c => (
              <option key={c.slug} value={c.slug}>{c.display_name}</option>
            ))}
            <option value="custom">Custom / other…</option>
          </select>
          {certSlug === 'custom' && (
            <input
              type="text"
              placeholder="e.g. AWS Solutions Architect Associate"
              value={customCertName}
              onChange={e => setCustomCertName(e.target.value)}
              className="mt-2 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          )}
        </div>

        {/* Mode toggle */}
        <div className="mb-4 flex gap-2">
          {(['flashcard', 'mcq'] as Mode[]).map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                mode === m
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-300 text-gray-600 hover:border-indigo-400'
              }`}
            >
              {m === 'flashcard' ? 'Flashcards' : 'MCQ Exam'}
            </button>
          ))}
        </div>

        {/* Text area */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Study material</label>
          <textarea
            rows={8}
            placeholder="Paste your notes, documentation, or any study material here…"
            value={text}
            onChange={e => setText(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={generating || !text.trim()}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {generating ? 'Generating…' : `Generate ${mode === 'flashcard' ? 'Flashcards' : 'MCQ Questions'}`}
        </button>

        {error && (
          <p className="mt-3 text-sm text-red-600">{error}</p>
        )}

        {/* Cards */}
        {cards.length > 0 && (
          <div className="mt-8 space-y-4">
            <p className="text-sm text-gray-500">
              {cards.length} {mode === 'flashcard' ? 'flashcard' : 'question'}{cards.length !== 1 ? 's' : ''}
              {generating ? ' — generating…' : ''}
            </p>
            {cards.map((card, i) =>
              isFlashcard(card) ? (
                <FlashcardView key={i} card={card} />
              ) : (
                <MCQView key={i} card={card as MCQQuestion} />
              )
            )}
          </div>
        )}
      </div>
    </div>
  )
}
