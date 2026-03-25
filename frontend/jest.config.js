export default {
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['./jest.setup.js'],
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  moduleNameMapper: {
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  extensionsToTreatAsEsm: ['.jsx'],
  coverageThreshold: {
    global: { lines: 70, functions: 70, branches: 60 },
  },
};
