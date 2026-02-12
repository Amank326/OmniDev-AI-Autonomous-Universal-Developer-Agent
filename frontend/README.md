# OmniDev AI Frontend

Modern React/Next.js frontend for OmniDev AI platform.

## Features

- 🎨 Beautiful dark-themed UI with Tailwind CSS
- 🔐 User authentication with JWT tokens
- 📊 Real-time dashboard with stats
- 🚀 Project and task management
- 🤖 AI agent orchestration
- 🔌 WebSocket real-time updates
- 📱 Responsive design

## Tech Stack

- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **API Client**: Axios
- **Icons**: Lucide React
- **Forms**: React Hook Form + Zod
- **Language**: TypeScript

## Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
# .env.local already configured to use localhost:8000
# For production, update:
NEXT_PUBLIC_API_URL=https://your-api-url
NEXT_PUBLIC_WS_URL=wss://your-ws-url
```

4. Start development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
src/
├── app/                 # Next.js App Router
│   ├── auth/           # Login/Signup pages
│   ├── dashboard/      # Main dashboard
│   └── layout.tsx      # Root layout
├── components/         # Reusable components
├── hooks/             # Custom React hooks
├── lib/               # Utilities (API client, etc)
├── store/             # Zustand state management
├── types/             # TypeScript type definitions
└── globals.css        # Global styles
```

## API Integration

The frontend connects to the backend API at `http://localhost:8000`:

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout

### Dashboard Endpoints
- `GET /api/stats` - Get dashboard statistics
- `GET /api/projects` - List user projects
- `GET /api/tasks` - List user tasks

## Building for Production

```bash
npm run build
npm run start
```

## Deployment

Ready for deployment to:
- Vercel (recommended)
- Netlify
- AWS Amplify
- Docker

## Demo Credentials

```
Email: demo@omnidev.ai
Password: demo123
```

## License

MIT
