import { useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Trash2, Eye, CheckCircle, Clock } from 'lucide-react'
import toast from 'react-hot-toast'

const Documents = () => {
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)

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

  async function fetchDocuments() {
    try {
      const response = await fetch('/api/documents/')
      if (response.ok) {
        const data = await response.json()
        setDocuments(data)
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
    }
  }

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
  }, [])

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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
        <p className="text-gray-600">
          Upload and manage your documents. Supported formats: CSV, PDF, TXT
        </p>
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
                      <div className="flex items-center">
                        {doc.processed ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                            <span className="text-green-600">Processed</span>
                          </>
                        ) : (
                          <>
                            <Clock className="w-4 h-4 text-yellow-500 mr-1" />
                            <span className="text-yellow-600">Processing</span>
                          </>
                        )}
                      </div>
                    </div>
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