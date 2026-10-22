/** @type {import('tailwindcss').Config} */
export default { darkMode:'class', content:['./index.html','./src/**/*.{ts,tsx}'],
theme:{ extend:{ colors:{
  neon:'#39FF14', neonHover:'#65FF45',
  ink:{bg:'#080B09',side:'#0D120F',surface:'#121914',elev:'#19221B',alt:'#1D2A24',input:'#101610',line:'#29352B'},
  mist:{bg:'#F7F9F6',side:'#FFFFFF',surface:'#FFFFFF',alt:'#EEF2ED',elev:'#F3F6F2',line:'#DCE4DC'},
  fg:'#F5F7F5', sub:'#A0ADA3', mute:'#78877C', dk:'#172019', dsub:'#5F6D62', pgreen:'#15803D', pgreenHover:'#166534'
}, fontFamily:{ sans:['Inter','system-ui','sans-serif'] }, boxShadow:{ glow:'0 0 18px rgba(57,255,20,.28)' } } }, plugins:[] }
