#!/bin/bash

echo "🔍 Verifying Frontend Agent 2 Setup..."
echo ""

# Check Node version
echo "✓ Checking Node.js version..."
node --version

# Check pnpm
echo "✓ Checking pnpm..."
pnpm --version

# Check key files exist
echo ""
echo "✓ Verifying core files..."

files=(
  "package.json"
  "tsconfig.json"
  "next.config.js"
  "tailwind.config.js"
  "app/layout.tsx"
  "app/providers.tsx"
  "components/command/command-palette.tsx"
  "components/ai-dock/ai-dock-content.tsx"
  "lib/commands/registry.ts"
  "lib/websocket/websocket-provider.tsx"
  "lib/shortcuts.ts"
  "lib/stores/ui-store.ts"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✅ $file"
  else
    echo "  ❌ Missing: $file"
  fi
done

echo ""
echo "✓ Setup verification complete!"
echo ""
echo "Next steps:"
echo "  1. Run: pnpm install"
echo "  2. Run: pnpm dev"
echo "  3. Open: http://localhost:3000"
echo "  4. Press: ⌘K to test Command Palette"
echo ""
