# Quick Start Guide

## Installation

```bash
# From repository root
cd /Users/isaacbuz/Documents/SWE
pnpm install
```

## Environment Setup

```bash
# Copy environment template
cp apps/web/.env.example apps/web/.env.local

# Edit if needed (optional - has defaults)
# NEXT_PUBLIC_WS_URL=http://localhost:4000
```

## Run Development Server

```bash
# From repository root
pnpm dev

# Or from apps/web
cd apps/web
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000)

## Try It Out

### Command Palette
- Press `⌘K` (or `Ctrl+K`)
- Type "spec" or "review"
- Use arrow keys, press Enter

### AI Dock
- Press `⌘/` (or `Ctrl+/`)
- Click through tabs
- Try suggestions

### Keyboard Shortcuts
- `⌘K` - Command Palette
- `⌘/` - AI Dock
- `Escape` - Close

## File Structure

```
apps/web/
├── components/
│   ├── command/          # Command Palette
│   └── ai-dock/          # AI Dock
├── lib/
│   ├── commands/         # Slash commands
│   ├── websocket/        # WebSocket
│   ├── stores/           # State
│   └── shortcuts.ts      # Shortcuts
└── app/
    └── (dashboard)/      # Main app
```

## Key Features

1. **Command Palette** - Universal search and command execution
2. **AI Dock** - Context-aware AI copilot
3. **Slash Commands** - /spec, /review, /deploy, /diagram
4. **WebSocket** - Real-time updates
5. **Keyboard Shortcuts** - Full keyboard navigation

## Documentation

- `README.md` - Complete documentation
- `IMPLEMENTATION_SUMMARY.md` - Detailed implementation notes
- `/docs/architecture/FRONTEND.md` - Design specifications

## Support

Check browser console for logs and errors.
