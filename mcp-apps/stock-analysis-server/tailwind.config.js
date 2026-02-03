/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./web/src/**/*.{js,ts,jsx,tsx}",
    "./web/*.html",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['SF Mono', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      colors: {
        stock: {
          up: '#10B981',
          down: '#EF4444',
          neutral: '#6B7280',
        },
      },
    },
  },
  plugins: [],
}
