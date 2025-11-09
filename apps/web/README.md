# AgentOS Web Application

Premium AI-native frontend built with Next.js 14, following the specifications in `/docs/architecture/FRONTEND.md`.

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The application will be available at `http://localhost:3000`.

## Architecture

### Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3 (Strict Mode)
- **Styling**: Tailwind CSS 3.4
- **State Management**: Zustand + TanStack Query
- **Icons**: Lucide React
- **Fonts**: Inter (body), General Sans (display), JetBrains Mono (code)

### Project Structure

```
apps/web/
├── app/                      # Next.js App Router
│   ├── (dashboard)/          # Main app layout group
│   │   ├── layout.tsx        # App shell layout
│   │   ├── page.tsx          # Home dashboard
│   │   ├── projects/         # Projects section
│   │   ├── agents/           # Agent roster
│   │   ├── analytics/        # Analytics dashboard
│   │   ├── integrations/     # External integrations
│   │   └── settings/         # Settings
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   └── app-shell/            # Core layout components
│       ├── top-navbar.tsx    # Top navigation bar
│       ├── left-rail.tsx     # Side navigation rail
│       └── ai-dock.tsx       # AI copilot dock
├── lib/
│   ├── theme/                # Theme system
│   │   ├── tokens.ts         # Design tokens
│   │   └── theme-provider.tsx # Theme context
│   └── utils/                # Utility functions
│       └── cn.ts             # Class name merger
└── public/                   # Static assets
```

## Design System

### Color Tokens

The application supports light and dark themes with the following color system:

- **Brand**: Primary action colors (indigo)
- **Ink**: Text colors (4 levels of hierarchy)
- **Surface**: Background colors (3 levels)
- **Border**: Border colors (3 weights)
- **Status**: Semantic colors (success, warning, danger, info)

### Spacing Scale

Based on a 4pt grid system (4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px)

### Typography

- **Display**: General Sans (headings, hero text)
- **Body**: Inter (all body text)
- **Mono**: JetBrains Mono (code, technical content)

## Features

### App Shell

- **Top Navbar**: Brand, navigation, command trigger, notifications, user menu
- **Left Rail**: Collapsible sidebar with workspace navigation
- **AI Dock**: Context-aware AI assistant panel (collapsible)
- **Responsive**: Mobile, tablet, and desktop layouts

### Routes

- `/` - Home dashboard with overview and AI suggestions
- `/projects` - Project list and management
- `/projects/[id]` - Project detail with board view
- `/agents` - Agent roster and crew composer
- `/analytics` - Metrics and performance dashboard
- `/integrations` - External service connections
- `/settings` - User preferences and theme settings

### Theme System

- Light, dark, and system theme modes
- Persistent theme selection (localStorage)
- Smooth transitions between themes
- CSS variables for dynamic theming

### Accessibility

- Keyboard navigation support
- Focus indicators
- Semantic HTML
- ARIA labels
- Screen reader compatible

## Next Steps

### Integration Tasks

1. **API Integration**: Connect to backend services (GraphQL/tRPC)
2. **State Management**: Set up Zustand stores and TanStack Query
3. **Authentication**: Implement auth flow and protected routes
4. **Real-time Updates**: WebSocket integration for live data
5. **Command Palette**: Build universal command/search interface
6. **Charts**: Add Recharts for analytics visualizations

### Component Development

1. Install shadcn/ui components library
2. Build reusable UI primitives (buttons, inputs, modals)
3. Create specialized components (command palette, diff viewer, crew composer)
4. Add form validation with React Hook Form + Zod

### Testing

1. Set up Vitest for unit tests
2. Add Playwright for E2E tests
3. Implement Testing Library for component tests
4. Add visual regression testing

### Performance

1. Implement code splitting and lazy loading
2. Optimize bundle size
3. Add performance monitoring
4. Implement caching strategies

## Environment Variables

Create a `.env.local` file with:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:4000
NEXT_PUBLIC_WS_URL=ws://localhost:4000

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

## Development Guidelines

### Code Style

- Follow TypeScript strict mode
- Use functional components with hooks
- Prefer composition over inheritance
- Keep components small and focused
- Use meaningful variable names

### Component Structure

```tsx
// 1. Imports
import { ComponentProps } from "react";

// 2. Types
interface MyComponentProps {
  // ...
}

// 3. Component
export function MyComponent({ ...props }: MyComponentProps) {
  // 4. Hooks
  // 5. Handlers
  // 6. Render
}
```

### Naming Conventions

- Components: PascalCase (e.g., `TopNavbar`)
- Functions: camelCase (e.g., `handleClick`)
- Files: kebab-case (e.g., `top-navbar.tsx`)
- CSS classes: Use Tailwind utilities

## License

Private - Internal use only
