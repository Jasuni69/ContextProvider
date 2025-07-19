import { MessageSquare, Github, Heart } from 'lucide-react'

const Footer = () => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">
                AI Document Chat
              </span>
            </div>
            <p className="text-gray-600 text-sm mb-4 max-w-md">
              Transform your documents into intelligent conversations. Upload, process, and chat with your content using advanced AI technology.
            </p>
            <div className="flex items-center space-x-4">
              <a
                href="https://github.com/Jasuni69/ContextProvider"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
              Quick Links
            </h3>
            <ul className="space-y-2">
              <li>
                <a href="/" className="text-gray-600 hover:text-primary-600 transition-colors duration-200 text-sm">
                  Home
                </a>
              </li>
              <li>
                <a href="/documents" className="text-gray-600 hover:text-primary-600 transition-colors duration-200 text-sm">
                  Upload Documents
                </a>
              </li>
              <li>
                <a href="/chat" className="text-gray-600 hover:text-primary-600 transition-colors duration-200 text-sm">
                  Start Chatting
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
              Support
            </h3>
            <ul className="space-y-2">
              <li>
                <span className="text-gray-600 text-sm">File Types:</span>
              </li>
              <li className="text-gray-500 text-xs ml-2">• PDF Documents</li>
              <li className="text-gray-500 text-xs ml-2">• CSV Files</li>
              <li className="text-gray-500 text-xs ml-2">• Text Files</li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500 text-sm">
              © {currentYear} AI Document Chat. Built with{' '}
              <Heart className="w-4 h-4 inline text-red-500" />
              {' '}using React & FastAPI.
            </p>
            <p className="text-gray-400 text-xs mt-2 md:mt-0">
              Powered by OpenAI & ChromaDB
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer 