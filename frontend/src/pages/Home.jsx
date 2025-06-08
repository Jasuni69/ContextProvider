import { Link } from 'react-router-dom'
import { Upload, MessageSquare, FileText, Brain, Search, Zap } from 'lucide-react'

const Home = () => {
  const features = [
    {
      icon: Upload,
      title: 'Upload Documents',
      description: 'Support for CSV, PDF, and TXT files with intelligent processing',
    },
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Advanced language models understand and analyze your content',
    },
    {
      icon: Search,
      title: 'Smart Search',
      description: 'Vector-based search finds relevant information across all documents',
    },
    {
      icon: MessageSquare,
      title: 'Natural Conversations',
      description: 'Ask questions in plain English and get intelligent responses',
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center">
            <Brain className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          AI-Powered Document Intelligence
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Upload your documents and have intelligent conversations about their content. 
          Our AI understands context and provides accurate, relevant answers to your questions.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/documents"
            className="btn-primary inline-flex items-center justify-center"
          >
            <Upload className="w-5 h-5 mr-2" />
            Upload Documents
          </Link>
          <Link
            to="/chat"
            className="btn-secondary inline-flex items-center justify-center"
          >
            <MessageSquare className="w-5 h-5 mr-2" />
            Start Chatting
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <div key={index} className="card text-center">
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <Icon className="w-6 h-6 text-primary-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {feature.description}
              </p>
            </div>
          )
        })}
      </div>

      {/* How it Works */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          How It Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-lg font-bold">
              1
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Upload</h3>
            <p className="text-gray-600 text-sm">
              Upload your CSV, PDF, or TXT files to get started
            </p>
          </div>
          <div className="text-center">
            <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-lg font-bold">
              2
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Process</h3>
            <p className="text-gray-600 text-sm">
              AI analyzes and creates searchable embeddings of your content
            </p>
          </div>
          <div className="text-center">
            <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-lg font-bold">
              3
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Ask</h3>
            <p className="text-gray-600 text-sm">
              Ask natural language questions and get intelligent answers
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home 