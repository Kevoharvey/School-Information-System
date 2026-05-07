// Tailwind CSS Configuration for Galala International School Portal

tailwind.config = {
  theme: {
    extend: {
      colors: {
        // Primary Colors
        'primary': '#1e40af',
        'primary-container': '#3b82f6',
        'on-primary': '#ffffff',
        'on-primary-container': '#ffffff',
        
        // Secondary Colors
        'secondary': '#7c3aed',
        'secondary-container': '#a78bfa',
        'secondary-fixed': '#ede9fe',
        'on-secondary': '#ffffff',
        'on-secondary-fixed': '#5b21b6',
        'on-secondary-fixed-variant': '#6d28d9',
        
        // Tertiary Colors
        'tertiary': '#059669',
        'tertiary-container': '#10b981',
        'tertiary-fixed': '#d1fae5',
        'on-tertiary': '#ffffff',
        'on-tertiary-fixed-variant': '#047857',
        
        // Error Colors
        'error': '#dc2626',
        'on-error': '#ffffff',
        
        // Background & Surface
        'background': '#f8fafc',
        'on-background': '#1e293b',
        'surface': '#ffffff',
        'surface-bright': '#ffffff',
        'surface-container': '#f1f5f9',
        'surface-container-low': '#f8fafc',
        'surface-container-high': '#e2e8f0',
        'surface-container-lowest': '#ffffff',
        'on-surface': '#1e293b',
        'on-surface-variant': '#64748b',
        
        // Outline Colors
        'outline': '#cbd5e1',
        'outline-variant': '#e2e8f0',
      },
      fontFamily: {
        'poppins': ['Poppins', 'sans-serif'],
        'inter': ['Inter', 'sans-serif'],
        'h1': ['Poppins', 'sans-serif'],
        'h2': ['Poppins', 'sans-serif'],
        'h3': ['Poppins', 'sans-serif'],
        'body-md': ['Inter', 'sans-serif'],
        'body-sm': ['Inter', 'sans-serif'],
        'caption': ['Inter', 'sans-serif'],
        'label-caps': ['Inter', 'sans-serif'],
      },
      fontSize: {
        'h1': ['2.5rem', { lineHeight: '1.2' }],
        'h2': ['2rem', { lineHeight: '1.3' }],
        'h3': ['1.5rem', { lineHeight: '1.4' }],
        'body-md': ['1rem', { lineHeight: '1.5' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        'caption': ['0.75rem', { lineHeight: '1.4' }],
        'label-caps': ['0.875rem', { lineHeight: '1.4' }],
      },
      spacing: {
        'stack-sm': '0.5rem',
        'stack-md': '1rem',
        'stack-lg': '1.5rem',
        'stack-xl': '2rem',
        'gutter': '1rem',
        'container-margin': '1.5rem',
      },
      borderRadius: {
        'sm': '0.375rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
        '2xl': '1.5rem',
      },
      boxShadow: {
        'sm': '0 1px 3px rgba(30, 41, 59, 0.05)',
        'md': '0 4px 6px rgba(30, 41, 59, 0.05)',
        'lg': '0 10px 15px rgba(30, 41, 59, 0.1)',
      },
    },
  },
  plugins: [],
}
