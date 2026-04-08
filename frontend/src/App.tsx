import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import DeckDetail from './pages/DeckDetail'
import Decks from './pages/Decks'
import Generate from './pages/Generate'

function Nav() {
  return (
    <nav className="border-b border-gray-200 bg-white px-6 py-3 flex items-center gap-6">
      <span className="font-bold text-indigo-700 text-lg">Quizine</span>
      <Link to="/decks" className="text-sm text-gray-600 hover:text-indigo-600">Decks</Link>
      <Link to="/generate" className="text-sm text-gray-600 hover:text-indigo-600">Generate</Link>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<Decks />} />
        <Route path="/decks" element={<Decks />} />
        <Route path="/decks/:id" element={<DeckDetail />} />
        <Route path="/generate" element={<Generate />} />
      </Routes>
    </BrowserRouter>
  )
}
