import Head from 'next/head'
import Link from 'next/link'

export default function Home() {
  return (
    <>
      <Head>
        <title>OmniDev AI - Autonomous Universal Developer Agent</title>
        <meta name="description" content="Production-ready AI platform with autonomous agents" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <h1 className="text-6xl font-bold text-gray-900 mb-4">
              OmniDev AI
            </h1>
            <p className="text-2xl text-gray-700 mb-8">
              Autonomous Universal Developer Agent
            </p>
            <p className="text-lg text-gray-600 mb-12 max-w-3xl mx-auto">
              Production-ready, full-stack platform featuring autonomous AI agents, 
              real-time collaboration, and scalable cloud-native architecture. 
              Built with FastAPI, Next.js, PostgreSQL, and Stripe.
            </p>

            <div className="flex justify-center gap-4 mb-16">
              <Link
                href="/auth/register"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition duration-200"
              >
                Get Started
              </Link>
              <Link
                href="/auth/login"
                className="bg-white hover:bg-gray-50 text-blue-600 font-semibold py-3 px-8 rounded-lg border-2 border-blue-600 transition duration-200"
              >
                Sign In
              </Link>
            </div>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              <div className="bg-white p-6 rounded-lg shadow-lg">
                <div className="text-4xl mb-4">🤖</div>
                <h3 className="text-xl font-semibold mb-2">AI Agents</h3>
                <p className="text-gray-600">
                  Autonomous agents for code analysis, generation, and documentation
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-lg">
                <div className="text-4xl mb-4">🔔</div>
                <h3 className="text-xl font-semibold mb-2">Multi-Channel Notifications</h3>
                <p className="text-gray-600">
                  Email, SMS, push notifications, and real-time WebSocket updates
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-lg">
                <div className="text-4xl mb-4">💳</div>
                <h3 className="text-xl font-semibold mb-2">Payment Integration</h3>
                <p className="text-gray-600">
                  Stripe-powered subscriptions and payment processing
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-lg">
                <div className="text-4xl mb-4">🔒</div>
                <h3 className="text-xl font-semibold mb-2">Secure Authentication</h3>
                <p className="text-gray-600">
                  JWT-based auth with email verification and password reset
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-lg">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-xl font-semibold mb-2">Real-Time Features</h3>
                <p className="text-gray-600">
                  WebSocket support for live collaboration and updates
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-lg">
                <div className="text-4xl mb-4">☁️</div>
                <h3 className="text-xl font-semibold mb-2">Cloud-Native</h3>
                <p className="text-gray-600">
                  Scalable architecture with Docker and Kubernetes
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
