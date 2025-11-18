import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import SessionsPage from './pages/SessionsPage'
import KanbanPage from './pages/KanbanPage'
import ObservabilityPage from './pages/ObservabilityPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="kanban" element={<KanbanPage />} />
          <Route path="observability" element={<ObservabilityPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
