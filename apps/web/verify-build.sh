#!/bin/bash

echo "==================================="
echo "Next.js App Verification Script"
echo "==================================="
echo ""

# Check if node_modules exists
if [ -d "node_modules" ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Dependencies not installed - run 'npm install'"
    exit 1
fi

# Check key files exist
echo ""
echo "Checking core files..."
files=(
    "package.json"
    "tsconfig.json"
    "tailwind.config.ts"
    "next.config.ts"
    "app/layout.tsx"
    "app/(dashboard)/layout.tsx"
    "components/app-shell/top-navbar.tsx"
    "components/app-shell/left-rail.tsx"
    "components/app-shell/ai-dock.tsx"
    "lib/theme/tokens.ts"
    "lib/theme/theme-provider.tsx"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file missing"
    fi
done

echo ""
echo "==================================="
echo "Ready to run!"
echo "==================================="
echo ""
echo "Commands:"
echo "  npm run dev      - Start development server"
echo "  npm run build    - Build for production"
echo "  npm run lint     - Run ESLint"
echo ""
