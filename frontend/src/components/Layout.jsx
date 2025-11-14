import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Chatbot from './Chatbot'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Determine current page based on route
  const getCurrentPage = () => {
    if (location.pathname.includes('bus-dashboard')) {
      return 'busDashboard'
    } else if (location.pathname.includes('manage-route')) {
      return 'manageRoute'
    }
    return 'busDashboard' // default
  }

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">M</div>
            <span className="logo-text">Movi</span>
          </div>
          <button 
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        
        <nav className="sidebar-nav">
          <Link 
            to="/bus-dashboard" 
            className={`nav-item ${location.pathname === '/bus-dashboard' ? 'active' : ''}`}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M3 4C3 3.44772 3.44772 3 4 3H16C16.5523 3 17 3.44772 17 4V16C17 16.5523 16.5523 17 16 17H4C3.44772 17 3 16.5523 3 16V4Z" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M3 8H17" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M7 3V17" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
            <span>Bus Dashboard</span>
          </Link>
          <Link 
            to="/manage-route" 
            className={`nav-item ${location.pathname === '/manage-route' ? 'active' : ''}`}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L2 7L10 12L18 7L10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 13L10 18L18 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 10L10 15L18 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Manage Route</span>
          </Link>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="main-wrapper">
        <main className="main-content">
          {children}
        </main>
      </div>

      {/* Chatbot */}
      <Chatbot currentPage={getCurrentPage()} />
    </div>
  )
}

export default Layout
