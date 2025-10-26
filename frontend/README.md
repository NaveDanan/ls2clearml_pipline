# Label Studio to ClearML Pipeline - Frontend

A beautiful Next.js dashboard for monitoring the Label Studio to ClearML pipeline in real-time.

## Features

- 🎨 Beautiful UI with Shadcn components and Tailwind CSS
- 🔄 Real-time status monitoring
- 📊 Interactive pipeline visualization
- ✨ Smooth animations with Framer Motion
- 🌙 Dark mode support
- 📱 Fully responsive design

## Getting Started

### Install Dependencies

```bash
npm install
# or
yarn install
# or
pnpm install
```

### Run Development Server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Configuration

The frontend connects to the FastAPI webhook server at `http://localhost:8000` by default. You can modify this in `next.config.js`.

## Components

- **PipelineFlow**: Animated flow diagram showing the pipeline stages
- **StatsPanel**: Real-time statistics cards
- **UI Components**: Reusable Shadcn components (Card, Button, etc.)

## Tech Stack

- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Shadcn UI**: Component library
- **Framer Motion**: Animations
- **Lucide React**: Icons
