module.exports = {
  testEnvironment: "jest-environment-jsdom",
  collectCoverage: true,
  coverageDirectory: "reports/coverage",
  coverageReporters: ["json", "text", "lcov", "clover"],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  reporters: [
    "default",
    ["jest-junit", { outputDirectory: "reports", outputName: "junit.xml" }]
  ],
  testMatch: [
    "**/tests/unit/**/*.test.js",
    "**/tests/integration/**/*.test.js",
    "**/tests/accessibility/**/*.test.js"
  ]
};
