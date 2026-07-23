module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    project: ["./tsconfig.json"],
    sourceType: "module",
  },
  plugins: ["@typescript-eslint", "n8n-nodes-base"],
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:n8n-nodes-base/community",
  ],
  ignorePatterns: ["dist/**", "node_modules/**", "*.js"],
  rules: {
    "@typescript-eslint/no-explicit-any": "off",
  },
};
