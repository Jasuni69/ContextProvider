import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, FileText, CheckCircle, Circle } from 'lucide-react'
import toast from 'react-hot-toast'

const Chat = () => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [documents, setDocuments] = useState([])
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    fetchDocuments()
    // Load initial welcome message
    setMessages([
      {
        id: 1,
        type: 'assistant',
        content: 'Hello! I\'m your AI assistant. I can help you find information from your uploaded documents. What would you like to know?',
        timestamp: new Date(),
      },
    ])
  }, [])

  async function fetchDocuments() {
    try {
      const response = await fetch('/api/documents/')
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.filter(doc => doc.processed))
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
    }
  }

  async function sendMessage() {
    if (!inputMessage.trim()) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          document_id: selectedDocumentId,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.response,
          timestamp: new Date(),
          sources: data.sources || [],
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to send message')
      }
    } catch (error) {
      toast.error('Error sending message')
      console.error('Error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
              <p className="text-gray-600">
                Ask questions about your documents ({documents.length} processed)
              </p>
            </div>
            {documents.length === 0 && (
              <div className="text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
                No documents available. Upload some documents first!
              </div>
            )}
          </div>
          
          {/* Document Selection */}
          {documents.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700">Select a document to chat about:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => setSelectedDocumentId(doc.id)}
                    className={`p-3 border rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md ${
                      selectedDocumentId === doc.id
                        ? 'border-primary-500 bg-primary-50 shadow-sm'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1 min-w-0">
                        <FileText className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {doc.original_filename}
                          </p>
                          <p className="text-xs text-gray-500">
                            {Math.round(doc.file_size / 1024)} KB • {doc.chunk_count} chunks
                          </p>
                        </div>
                      </div>
                      <div className="flex-shrink-0 ml-2">
                        {selectedDocumentId === doc.id ? (
                          <CheckCircle className="w-5 h-5 text-primary-600" />
                        ) : (
                          <Circle className="w-5 h-5 text-gray-300" />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Selected Document Info */}
              {selectedDocumentId && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm text-green-800">
                      Ready to chat about: <strong>
                        {documents.find(doc => doc.id === selectedDocumentId)?.original_filename}
                      </strong>
                    </span>
                  </div>
                </div>
              )}
              
              {/* No Selection Warning */}
              {!selectedDocumentId && (
                <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Circle className="w-4 h-4 text-amber-600" />
                    <span className="text-sm text-amber-800">
                      Please select a document above to start chatting about it
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`chat-message ${message.type} max-w-3xl ${
                  message.type === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    {message.type === 'user' ? (
                      <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4" />
                      </div>
                    ) : (
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <Bot className="w-4 h-4 text-primary-600" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="prose prose-sm max-w-none">
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-500 mb-2">Sources:</p>
                        <div className="space-y-1">
                          {message.sources.map((source, index) => (
                            <div
                              key={index}
                              className="flex items-center text-xs text-gray-600"
                            >
                              <FileText className="w-3 h-3 mr-1" />
                              <span>{source}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="mt-2">
                      <span
                        className={`text-xs ${
                          message.type === 'user' ? 'text-white text-opacity-70' : 'text-gray-500'
                        }`}
                      >
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="chat-message assistant bg-white border border-gray-200">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <Bot className="w-4 h-4 text-primary-600" />
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-gray-500 text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  selectedDocumentId 
                    ? `Ask questions about ${documents.find(doc => doc.id === selectedDocumentId)?.original_filename}...`
                    : documents.length > 0 
                      ? "Select a document above, then ask questions about it..."
                      : "Upload documents first to start chatting..."
                }
                className="input-field resize-none"
                rows="2"
                disabled={isLoading || documents.length === 0 || !selectedDocumentId}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading || documents.length === 0 || !selectedDocumentId}
              className="btn-primary self-end flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          
          {/* Status Messages */}
          {documents.length === 0 && (
            <p className="text-sm text-gray-500 mt-2">
              Upload and process some documents to start chatting!
            </p>
          )}
          
          {documents.length > 0 && !selectedDocumentId && (
            <p className="text-sm text-amber-600 mt-2">
              Select a document above to start asking questions about it.
            </p>
          )}
          
          {selectedDocumentId && (
            <p className="text-sm text-green-600 mt-2">
              Ready to chat about {documents.find(doc => doc.id === selectedDocumentId)?.original_filename}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Chat 