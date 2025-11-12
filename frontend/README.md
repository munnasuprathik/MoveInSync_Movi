# Movi Frontend

React frontend for Movi transport management system.

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5000

## Pages

- **Bus Dashboard** (`/bus-dashboard`): View all trips and their deployments
- **Manage Route** (`/manage-route`): Manage stops, paths, and routes

## Features

- ✅ React Router for navigation
- ✅ Axios for API calls
- ✅ Responsive design
- ✅ Modern UI with CSS
- ✅ Real-time data fetching

## API Integration

All API calls are configured in `src/services/api.js` and connect to the backend at `http://localhost:5005/api`

