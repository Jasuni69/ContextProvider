import { useState, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Trash2, Eye, CheckCircle, Clock, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

const Documents = () => {
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const refreshIntervalRef = useRef(null)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'application/pdf': ['.pdf'],
    },
    maxSize: 10485760, // 10MB
    onDrop: handleFileUpload,
  })

  async function handleFileUpload(acceptedFiles) {
    setUploading(true)
    
    for (const file of acceptedFiles) {
      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch('/api/documents/upload', {
          method: 'POST',
          body: formData,
        })

        if (response.ok) {
          const result = await response.json()
          toast.success(`${file.name} uploaded successfully!`)
          fetchDocuments() // Refresh the documents list
        } else {
          const error = await response.json()
          toast.error(`Failed to upload ${file.name}: ${error.detail}`)
        }
      } catch (error) {
        toast.error(`Error uploading ${file.name}: ${error.message}`)
      }
    }
    
    setUploading(false)
  }

  async function fetchDocuments(showRefreshing = false) {
    try {
      if (showRefreshing) setRefreshing(true)
      const response = await fetch('/api/documents/')
      if (response.ok) {
        const data = await response.json()
        setDocuments(data)
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      if (showRefreshing) setRefreshing(false)
    }
  }

  const handleManualRefresh = () => {
    fetchDocuments(true)
  }

  // Check if there are any processing documents to determine if we should continue polling
  const hasProcessingDocuments = documents.some(doc => !doc.processed && !doc.processing_error)

  async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        toast.success('Document deleted successfully!')
        fetchDocuments()
      } else {
        toast.error('Failed to delete document')
      }
    } catch (error) {
      toast.error('Error deleting document')
    }
  }

  useEffect(() => {
    fetchDocuments()
    
    // Only set up interval if there are processing documents
    if (hasProcessingDocuments) {
      refreshIntervalRef.current = setInterval(() => fetchDocuments(), 3000) // Refresh every 3 seconds
    } else {
      clearInterval(refreshIntervalRef.current)
    }
    
    return () => clearInterval(refreshIntervalRef.current)
  }, [hasProcessingDocuments])

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = (fileType) => {
    return <FileText className="w-8 h-8 text-primary-600" />
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
            <p className="text-gray-600">
              Upload and manage your documents. Supported formats: CSV, PDF, TXT
            </p>
            {hasProcessingDocuments && (
              <p className="text-sm text-blue-600 mt-1 flex items-center">
                <Clock className="w-4 h-4 mr-1 animate-spin" />
                {documents.filter(doc => !doc.processed && !doc.processing_error).length} document(s) processing... (auto-refreshing)
              </p>
            )}
          </div>
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Upload Area */}
      <div className="mb-8">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center">
            <Upload className="w-12 h-12 text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-lg text-primary-600 font-medium">
                Drop the files here...
              </p>
            ) : (
              <>
                <p className="text-lg text-gray-600 mb-2">
                  Drag & drop files here, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Supports CSV, PDF, and TXT files up to 10MB
                </p>
              </>
            )}
          </div>
        </div>
        {uploading && (
          <div className="mt-4 text-center">
            <div className="inline-flex items-center text-primary-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
              Uploading files...
            </div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Your Documents ({documents.length})
        </h2>
        
        {documents.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg mb-2">No documents uploaded yet</p>
            <p className="text-gray-400">Upload your first document to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                <div className="flex items-center space-x-4">
                  {getFileIcon(doc.file_type)}
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {doc.original_filename}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
                      <span>•</span>
                      
                      {/* Status with Progress */}
                      <div className="flex items-center space-x-2">
                        {doc.processing_error ? (
                          <>
                            <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                              <span className="text-white text-xs">✕</span>
                            </div>
                            <span className="text-red-600">Failed</span>
                          </>
                        ) : doc.processed ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-green-600">Processed ({doc.chunk_count} chunks)</span>
                          </>
                        ) : (
                          <>
                            <div className="flex items-center space-x-2">
                              <div className="relative">
                                <Clock className="w-4 h-4 text-blue-500 animate-spin" />
                              </div>
                              <span className="text-blue-600">Processing...</span>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                    
                    {/* Progress Bar for Processing Documents */}
                    {!doc.processed && !doc.processing_error && (
                      <div className="mt-2">
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span>Processing document</span>
                        </div>
                        <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                        </div>
                      </div>
                    )}
                    
                    {/* Error Details */}
                    {doc.processing_error && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                        <strong>Error:</strong> {doc.processing_error}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => deleteDocument(doc.id)}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors duration-200"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Documents 