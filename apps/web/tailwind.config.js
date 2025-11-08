/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['General Sans', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          primary: '#4F46E5',
          hover: '#4338CA',
          active: '#3730A3',
        },
        ink: {
          primary: '#0B1020',
          secondary: '#374151',
          tertiary: '#6B7280',
          disabled: '#9CA3AF',
        },
      },
    },
  },
  plugins: [],
}
