import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createDeck, DeckSummary, listDecks } from '../api/decks'

export default function Decks() {
  const navigate = useNavigate()
  const [decks, setDecks] = useState<DeckSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // New deck form
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [customName, setCustomName] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    listDecks()
      .then(setDecks)
      .catch(() => setError('Could not load decks'))
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    setCreating(true)
    try {
      const deck = await createDeck({
        title: title.trim(),
        custom_cert_name: customName.trim() || undefined,
      })
      navigate(`/decks/${deck.id}`)
    } catch {
      setError('Failed to create deck')
      setCreating(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">My Decks</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm font-medium"
        >
          + New Deck
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="mb-6 p-4 border border-gray-200 rounded-xl bg-gray-50">
          <div className="mb-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              placeholder="e.g. Databricks ML Study"
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Certification (optional)</label>
            <input
              value={customName}
              onChange={e => setCustomName(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              placeholder="e.g. AWS Data Engineer Associate"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={creating}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {creating ? 'Creating…' : 'Create'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {loading ? (
        <p className="text-gray-500 text-sm">Loading…</p>
      ) : decks.length === 0 ? (
        <p className="text-gray-500 text-sm">No decks yet. Create one above.</p>
      ) : (
        <ul className="space-y-3">
          {decks.map(deck => (
            <li key={deck.id}>
              <Link
                to={`/decks/${deck.id}`}
                className="block p-4 border border-gray-200 rounded-xl hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
              >
                <div className="font-medium text-gray-900">{deck.title}</div>
                {deck.custom_cert_name && (
                  <div className="text-sm text-gray-500 mt-0.5">{deck.custom_cert_name}</div>
                )}
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(deck.created_at).toLocaleDateString()}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
