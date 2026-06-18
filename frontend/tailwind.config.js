/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17262b",
        mint: "#0f766e",
        clay: "#f97316",
        paper: "#f7f4ef",
      },
      boxShadow: {
        soft: "0 18px 60px rgba(23, 38, 43, 0.12)",
      },
    },
  },
  plugins: [],
};
