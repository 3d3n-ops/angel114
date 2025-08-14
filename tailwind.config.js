/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        'jetbrains': ['JetBrains Mono', 'monospace'],
        'inter': ['Inter', 'sans-serif'],
      },
      keyframes: {
        fadeInUp: {
          '0%': {
            opacity: '0',
            transform: 'translateY(20px)'
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)'
          }
        },
        float: {
          '0%, 100%': {
            transform: 'translateY(0px)'
          },
          '50%': {
            transform: 'translateY(-20px)'
          }
        },
        floatSide: {
          '0%, 100%': {
            transform: 'translateX(0px)'
          },
          '50%': {
            transform: 'translateX(-15px)'
          }
        }
      },
      animation: {
        'fadeInUp': 'fadeInUp 0.5s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'floatSide': 'floatSide 3.5s ease-in-out infinite 0.5s'
      }
    },
  },
  plugins: [],
  darkMode: 'class',
}
