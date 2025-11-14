import React, { useState, useRef, useEffect } from 'react'
import { agentAPI } from '../services/api'
import './Chatbot.css'

function Chatbot({ currentPage = 'busDashboard' }) {
  // Generate a unique session ID for this chat session
  const [sessionId] = useState(() => {
    // Get existing session ID from localStorage or create new one
    const stored = localStorage.getItem('movi_chat_session_id')
    if (stored) return stored
    const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    localStorage.setItem('movi_chat_session_id', newId)
    return newId
  })

  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m Movi, your transport management assistant. How can I help you today?'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [speechRecognitionAvailable, setSpeechRecognitionAvailable] = useState(false)
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)
  const synthRef = useRef(null)
  const fileInputRef = useRef(null)
  

  // Initialize speech recognition and synthesis once on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Initialize speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      try {
        recognitionRef.current = new SpeechRecognition()
        recognitionRef.current.continuous = false
        recognitionRef.current.interimResults = false
        recognitionRef.current.lang = 'en-US'

        recognitionRef.current.onresult = (event) => {
          if (event.results && event.results.length > 0 && event.results[0].length > 0) {
            const transcript = event.results[0][0].transcript
            setInput(prev => prev + (prev ? ' ' : '') + transcript)
          }
          setIsListening(false)
        }

        recognitionRef.current.onerror = (event) => {
          console.error('Speech recognition error:', event.error)
          setIsListening(false)
          
          let errorMessage = 'Speech recognition error. '
          switch (event.error) {
            case 'not-allowed':
              errorMessage = 'Microphone access denied. Please allow microphone access in your browser settings and try again.'
              break
            case 'no-speech':
              errorMessage = 'No speech detected. Please try again.'
              break
            case 'audio-capture':
              errorMessage = 'No microphone found. Please check your microphone connection.'
              break
            case 'network':
              errorMessage = 'Network error. Please check your internet connection.'
              break
            case 'aborted':
              // User stopped, no need to show error
              return
            default:
              errorMessage = `Speech recognition error: ${event.error}. Please try again.`
          }
          
          // Show error in chat instead of alert
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: errorMessage
          }])
        }

        recognitionRef.current.onend = () => {
          setIsListening(false)
        }

        setSpeechRecognitionAvailable(true)
      } catch (error) {
        console.error('Failed to initialize speech recognition:', error)
        setSpeechRecognitionAvailable(false)
      }
    } else {
      setSpeechRecognitionAvailable(false)
    }

    // Initialize speech synthesis
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis
    }
  }, []) // Empty dependency array - only run once on mount

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input.trim() }
    const currentInput = input.trim()
    
    // Add user message to state immediately for UI
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Call new agent API with currentPage and sessionId
      const response = await agentAPI.chat(currentInput, currentPage, sessionId)

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response || 'Sorry, I could not generate a response.'
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Update awaiting confirmation status
      setAwaitingConfirmation(response.data.awaiting_confirmation || false)
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Sorry, I encountered an error. Please try again.'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: errorMessage
      }])
      setAwaitingConfirmation(false)
    } finally {
      setIsLoading(false)
    }
  }


  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSpeechToText = () => {
    if (!speechRecognitionAvailable || !recognitionRef.current) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Speech recognition is not supported in your browser or requires HTTPS. Please use Chrome, Edge, or Safari, and ensure you are accessing the site over HTTPS.'
      }])
      return
    }

    if (isListening) {
      try {
        recognitionRef.current.stop()
        setIsListening(false)
      } catch (error) {
        console.error('Error stopping recognition:', error)
        setIsListening(false)
      }
    } else {
      try {
        setIsListening(true)
        recognitionRef.current.start()
      } catch (error) {
        console.error('Error starting recognition:', error)
        setIsListening(false)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Failed to start speech recognition. Please check your microphone permissions and try again.'
        }])
      }
    }
  }

  const handleTextToSpeech = (text) => {
    if (!synthRef.current && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis
    }

    if (!synthRef.current) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Text-to-speech is not supported in your browser.'
      }])
      return
    }

    if (isSpeaking) {
      synthRef.current.cancel()
      setIsSpeaking(false)
    } else {
      try {
        setIsSpeaking(true)
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.onend = () => setIsSpeaking(false)
        utterance.onerror = (event) => {
          console.error('Speech synthesis error:', event.error)
          setIsSpeaking(false)
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: 'Text-to-speech error. Please try again.'
          }])
        }
        synthRef.current.speak(utterance)
      } catch (error) {
        console.error('Error starting speech synthesis:', error)
        setIsSpeaking(false)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Failed to start text-to-speech. Please try again.'
        }])
      }
    }
  }

  const handleStopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel()
      setIsSpeaking(false)
    }
  }

  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Please select an image file (PNG, JPG, etc.)'
        }])
        return
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Image file is too large. Please select an image smaller than 10MB.'
        }])
        return
      }

      setSelectedImage(file)
      
      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleImageUpload = async () => {
    if (!selectedImage || !input.trim()) {
      if (!selectedImage) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Please select an image first.'
        }])
      }
      if (!input.trim()) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Please provide a message describing what you want to do with the image.'
        }])
      }
      return
    }

    const userMessage = { 
      role: 'user', 
      content: input.trim(),
      image: imagePreview
    }
    
    // Add user message with image preview to state
    setMessages(prev => [...prev, userMessage])
    const currentInput = input.trim()
    const currentImage = selectedImage
    
    // Clear input and image
    setInput('')
    setSelectedImage(null)
    setImagePreview(null)
    setIsLoading(true)

    try {
      // Call image upload API
      const response = await agentAPI.uploadImage(currentImage, currentInput, currentPage, sessionId)

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response || 'Image processed successfully!'
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Update awaiting confirmation status
      setAwaitingConfirmation(response.data.awaiting_confirmation || false)
    } catch (error) {
      console.error('Image upload error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Sorry, I encountered an error processing the image. Please try again.'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: errorMessage
      }])
      setAwaitingConfirmation(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemoveImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button 
          className="chatbot-toggle"
          onClick={() => setIsOpen(true)}
          aria-label="Open chatbot"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      )}

      {/* Chatbot Panel */}
      {isOpen && (
        <div className="chatbot-container">
          <div className="chatbot-header">
            <div className="chatbot-title">
              <h3>AI Assistant</h3>
              <span className="chatbot-status">Online</span>
            </div>
            <button 
              className="chatbot-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chatbot"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-content">
                  {message.image && (
                    <div style={{ marginBottom: '8px', borderRadius: '8px', overflow: 'hidden' }}>
                      <img 
                        src={message.image} 
                        alt="Uploaded" 
                        style={{ 
                          maxWidth: '100%', 
                          maxHeight: '200px', 
                          objectFit: 'contain',
                          borderRadius: '8px'
                        }} 
                      />
                    </div>
                  )}
                  {message.content}
                </div>
                {message.role === 'assistant' && (
                  <button
                    className="message-tts-btn"
                    onClick={() => handleTextToSpeech(message.content)}
                    title="Read aloud"
                  >
                    <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                      <path d="M6 4L6 16L14 10L6 4Z" fill="currentColor"/>
                    </svg>
                  </button>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="message assistant">
                <div className="message-content loading">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {isSpeaking && (
            <div className="chatbot-speaking-indicator">
              <span>Speaking...</span>
              <button onClick={handleStopSpeaking} className="stop-speaking-btn">Stop</button>
            </div>
          )}

          {awaitingConfirmation && (
            <div className="chatbot-confirmation-indicator" style={{
              padding: '8px 12px',
              margin: '8px 16px',
              backgroundColor: '#fef3c7',
              border: '1px solid #fbbf24',
              borderRadius: '8px',
              fontSize: '14px',
              color: '#92400e'
            }}>
              ⚠️ Waiting for your confirmation. Reply 'yes' to proceed or 'no' to cancel.
            </div>
          )}

          <div className="chatbot-input-container">
            {/* Image Preview */}
            {imagePreview && (
              <div style={{
                padding: '8px 12px',
                margin: '8px 16px',
                backgroundColor: '#f3f4f6',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <img 
                  src={imagePreview} 
                  alt="Preview" 
                  style={{ 
                    width: '40px', 
                    height: '40px', 
                    objectFit: 'cover',
                    borderRadius: '4px'
                  }} 
                />
                <span style={{ flex: 1, fontSize: '14px', color: '#374151' }}>
                  Image selected
                </span>
                <button
                  onClick={handleRemoveImage}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    color: '#ef4444'
                  }}
                  title="Remove image"
                >
                  <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                    <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </button>
              </div>
            )}

            <div className="chatbot-input-wrapper">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                ref={fileInputRef}
                style={{ display: 'none' }}
              />
              <button
                className={`chatbot-mic-btn ${isListening ? 'listening' : ''} ${!speechRecognitionAvailable ? 'disabled' : ''}`}
                onClick={handleSpeechToText}
                title={!speechRecognitionAvailable ? 'Speech recognition not available' : (isListening ? 'Stop listening' : 'Start voice input')}
                disabled={isLoading || !speechRecognitionAvailable}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 1C8.9 1 8 1.9 8 3V9C8 10.1 8.9 11 10 11C11.1 11 12 10.1 12 9V3C12 1.9 11.1 1 10 1Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M16 9C16 12.3 13.3 15 10 15M10 15V17M10 17H7M10 17H13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <button
                className="chatbot-image-btn"
                onClick={() => fileInputRef.current?.click()}
                title="Upload image"
                disabled={isLoading}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#6b7280',
                  transition: 'color 0.2s'
                }}
                onMouseEnter={(e) => e.target.style.color = '#3b82f6'}
                onMouseLeave={(e) => e.target.style.color = '#6b7280'}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M4 16L8.586 11.414C9.367 10.633 10.633 10.633 11.414 11.414L16 16M14 14L15.586 12.414C16.367 11.633 17.633 11.633 18.414 12.414L20 14M14 8H14.01M6 20H14C15.1046 20 16 19.1046 16 18V6C16 4.89543 15.1046 4 14 4H6C4.89543 4 4 4.89543 4 6V18C4 19.1046 4.89543 20 6 20Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <textarea
                className="chatbot-input"
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  // Auto-resize textarea
                  e.target.style.height = 'auto'
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
                }}
                onKeyPress={handleKeyPress}
                placeholder={awaitingConfirmation ? "Reply 'yes' to confirm or 'no' to cancel..." : selectedImage ? "Describe what you want to do with this image..." : "Type your message or use voice input..."}
                rows="1"
                disabled={isLoading}
              />
              <button
                className="chatbot-send-btn"
                onClick={selectedImage ? handleImageUpload : handleSend}
                disabled={(!input.trim() && !selectedImage) || isLoading}
                title={selectedImage ? "Send image with message" : "Send message"}
              >
                {isLoading ? (
                  <svg className="spinner" width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="31.416" strokeDashoffset="31.416">
                      <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416;0 31.416" repeatCount="indefinite"/>
                      <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416;-31.416" repeatCount="indefinite"/>
                    </circle>
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </button>
            </div>
            {isListening && (
              <div className="listening-indicator">
                <span className="pulse"></span>
                Listening...
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

export default Chatbot

