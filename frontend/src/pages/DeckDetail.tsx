import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { approveCard, CardResponse, deleteCard, updateCard } from '../api/cards'
import { getDeck, DeckDetail as DeckDetailType } from '../api/decks'

function CardEditor({
  card,
  onUpdate,
  onDelete,
}: {
  card: CardResponse
  onUpdate: (updated: CardResponse) => void
  onDelete: (id: number) => void
}) {
  const [editing, setEditing] = useState(false)
  const [front, setFront] = useState(card.front ?? '')
  const [back, setBack] = useState(card.back ?? '')
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    setSaving(true)
    try {
      const updated = await updateCard(card.id, { front, back })
      onUpdate(updated)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  async function handleApprove() {
    const updated = await approveCard(card.id)
    onUpdate(updated)
  }

  async function handleDelete() {
    await deleteCard(card.id)
    onDelete(card.id)
  }

  return (
    <div className={`border rounded-xl p-4 ${card.approved ? 'border-green-300 bg-green-50' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{card.type}</span>
        <div className="flex gap-1.5 shrink-0">
          {!card.approved && (
            <button
              onClick={handleApprove}
              className="text-xs px-2 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200"
            >
              Approve
            </button>
          )}
          <button
            onClick={() => setEditing(!editing)}
            className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
          >
            {editing ? 'Cancel' : 'Edit'}
          </button>
          <button
            onClick={handleDelete}
            className="text-xs px-2 py-1 rounded bg-red-100 text-red-600 hover:bg-red-200"
          >
            Delete
          </button>
        </div>
      </div>

      {editing ? (
        <div className="space-y-2">
          <textarea
            value={front}
            onChange={e => setFront(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
            rows={2}
            placeholder="Front / Question"
          />
          {card.type === 'flashcard' && (
            <textarea
              value={back}
              onChange={e => setBack(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
              rows={2}
              placeholder="Back / Answer"
            />
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="text-sm bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      ) : (
        <div className="space-y-1">
          <p className="text-sm text-gray-800 font-medium">{card.front}</p>
          {card.back && <p className="text-sm text-gray-500">{card.back}</p>}
          {card.custom_topic_tag && (
            <span className="inline-block text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
              {card.custom_topic_tag}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default function DeckDetailPage() {
  const { id } = useParams<{ id: string }>()
  const deckId = Number(id)

  const [deck, setDeck] = useState<DeckDetailType | null>(null)
  const [cards, setCards] = useState<CardResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDeck(deckId)
      .then(setDeck)
      .catch(() => setError('Could not load deck'))
      .finally(() => setLoading(false))
  }, [deckId])

  function handleCardUpdate(updated: CardResponse) {
    setCards(prev => prev.map(c => (c.id === updated.id ? updated : c)))
  }

  function handleCardDelete(cardId: number) {
    setCards(prev => prev.filter(c => c.id !== cardId))
  }

  if (loading) return <div className="p-6 text-gray-500 text-sm">Loading…</div>
  if (error || !deck) return <div className="p-6 text-red-500 text-sm">{error ?? 'Not found'}</div>

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-4">
        <Link to="/decks" className="text-sm text-indigo-600 hover:underline">← All Decks</Link>
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{deck.title}</h1>
        {deck.cert_display_name && (
          <p className="text-sm text-gray-500 mt-1">{deck.cert_display_name}</p>
        )}
        {deck.custom_cert_name && !deck.cert_display_name && (
          <p className="text-sm text-gray-500 mt-1">{deck.custom_cert_name}</p>
        )}
        <p className="text-xs text-gray-400 mt-1">{deck.card_count} cards</p>
      </div>

      <div className="mb-4 flex gap-2">
        <Link
          to={`/generate?deck_id=${deck.id}`}
          className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          Generate Cards
        </Link>
      </div>

      {cards.length === 0 ? (
        <p className="text-gray-500 text-sm">No cards yet. Generate some above.</p>
      ) : (
        <div className="space-y-3">
          {cards.map(card => (
            <CardEditor
              key={card.id}
              card={card}
              onUpdate={handleCardUpdate}
              onDelete={handleCardDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
