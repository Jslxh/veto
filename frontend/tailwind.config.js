/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#12151C",
        darkPanel: "#181B24",
        proposeGreen: "#10B981",
        declineAmber: "#F59E0B",
        declineRed: "#EF4444",
      }
    },
  },
  plugins: [],
}
