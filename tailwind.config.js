/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './otosapp/templates/**/*.html',
    './static/**/*.js',
    './node_modules/flowbite/**/*.js',
    "./layouts/**/*.html", 
    "./content/**/*.md", 
    "./content/**/*.html", 
    "./src/**/*.js"
  ],
  safelist: [
    'w-64',
    'w-1/2',
    'rounded-l-lg',
    'rounded-r-lg',
    'bg-gray-200',
    'grid-cols-4',
    'grid-cols-7',
    'h-6',
    'leading-6',
    'h-9',
    'leading-9',
    'shadow-lg',
    'bg-green-600',
    'bg-indigo-600',
    'bg-yellow-100',
    'bg-yellow-200',
    'bg-yellow-600',
    'text-yellow-600',
    'text-yellow-700',
    'border-yellow-200',
    'border-yellow-700',
    'dark:bg-yellow-900/30',
    'dark:text-yellow-400',
    'dark:border-yellow-700',
    'rotate-180'
  ],

  // Ensure dynamic role badge classes aren't purged by Tailwind's optimizer
  // These classes are constructed in templates by a custom tag and may not
  // be discoverable by static analysis.
  safelist: [
    'bg-pink-100', 'text-pink-800', 'dark:bg-pink-900', 'dark:text-pink-100', 'bg-pink-200/50',
    'bg-purple-100', 'text-purple-800', 'dark:bg-purple-900', 'dark:text-purple-100', 'bg-purple-200/50',
    'bg-teal-100', 'text-teal-800', 'dark:bg-teal-900', 'dark:text-teal-100', 'bg-teal-200/50',
    'bg-yellow-100', 'text-yellow-800', 'dark:bg-yellow-900', 'dark:text-yellow-100', 'bg-yellow-200/50',
    // common utility classes used by the tag
    'px-2', 'py-0.5', 'text-xs', 'px-3', 'py-1', 'text-sm', 'font-medium', 'rounded-full'
  ],

  darkMode: 'class',

  theme: {
    extend: {
      colors: {
        primary: {"50":"#eff6ff","100":"#dbeafe","200":"#bfdbfe","300":"#93c5fd","400":"#60a5fa","500":"#3b82f6","600":"#2563eb","700":"#1d4ed8","800":"#1e40af","900":"#1e3a8a","950":"#172554"}
      },
      fontFamily: {
        'body': [
          'Inter', 
          'ui-sans-serif', 
          'system-ui', 
          '-apple-system', 
          'system-ui', 
          'Segoe UI', 
          'Roboto', 
          'Helvetica Neue', 
          'Arial', 
          'Noto Sans',  
          'sans-serif', 
          'Apple Color Emoji', 
          'Segoe UI Emoji', 
          'Segoe UI Symbol', 
          'Noto Color Emoji'
        ],

        sans: [
          'Graphik',
          'Inter', 
          'ui-sans-serif', 
          'system-ui', 
          '-apple-system', 
          'system-ui', 
          'Segoe UI', 
          'Roboto', 
          'Helvetica Neue', 
          'Arial', 
          'Noto Sans', 
          'sans-serif', 
          'Apple Color Emoji', 
          'Segoe UI Emoji', 
          'Segoe UI Symbol', 
          'Noto Color Emoji',
        ],
        serif: ['Merriweather', 'serif'],
      },
      extend: {
        spacing: {
          '128': '32rem',
          '144': '36rem',
        },
        borderRadius: {
          '4xl': '2rem',
        },
    },
  },
},
plugins: [
  require('flowbite/plugin')
],
}


