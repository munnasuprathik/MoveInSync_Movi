import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import BusDashboard from './pages/BusDashboard'
import ManageRoute from './pages/ManageRoute'
import Layout from './components/Layout'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/bus-dashboard" replace />} />
          <Route path="/bus-dashboard" element={<BusDashboard />} />
          <Route path="/manage-route" element={<ManageRoute />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

