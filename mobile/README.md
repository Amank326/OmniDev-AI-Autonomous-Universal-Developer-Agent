# OmniDev AI Mobile App

Cross-platform mobile application for OmniDev AI built with React Native and Expo.

## Features

- 📱 iOS and Android support
- 🔐 Secure authentication
- 📊 Dashboard with live stats
- 🚀 Project management
- 🤖 Agent orchestration
- 🔔 Real-time notifications
- 📲 Responsive mobile UI

## Tech Stack

- **Framework**: React Native + Expo
- **Navigation**: React Navigation
- **State Management**: Zustand
- **Styling**: NativeWind (Tailwind for React Native)
- **API Client**: Axios
- **Storage**: Async Storage
- **Language**: TypeScript

## Installation

### Prerequisites
- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- Expo Go app (iOS/Android) or simulators

### Setup

1. Navigate to mobile directory:
```bash
cd mobile
```

2. Install dependencies:
```bash
npm install
```

3. Configure API endpoint:
```bash
# Update src/lib/api.ts with your backend URL
const API_URL = 'http://your-backend-url:8000';
```

4. Start Expo development server:
```bash
npm run start
```

5. Run on device or simulator:
```bash
# iOS simulator
npm run ios

# Android emulator
npm run android

# Web (testing)
npm run web
```

## Building for Production

### iOS Build
```bash
eas build --platform ios
```

### Android Build
```bash
eas build --platform android
```

### Publish
```bash
eas submit
```

## Project Structure

```
mobile/
├── screens/
│   ├── auth/
│   │   ├── LoginScreen.tsx
│   │   └── SignupScreen.tsx
│   ├── dashboard/
│   │   └── DashboardScreen.tsx
│   ├── projects/
│   │   └── ProjectsScreen.tsx
│   ├── agents/
│   │   └── AgentsScreen.tsx
│   └── settings/
│       └── SettingsScreen.tsx
├── lib/
│   ├── api.ts
│   └── storage.ts
├── hooks/
│   └── useAuth.ts
├── store/
│   └── auth.ts
├── App.tsx
└── app.json
```

## Available Screens

- **Authentication**: Login and signup
- **Dashboard**: Overview and statistics
- **Projects**: Manage AI projects
- **Agents**: View and control AI agents
- **Settings**: User preferences and account

## Demo Credentials

```
Email: demo@omnidev.ai
Password: demo123
```

## License

MIT
