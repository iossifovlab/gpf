const esModules = ['d3', 'd3-array', 'internmap', 'delaunator', 'robust-predicates'].join('|');

module.exports = {
  preset: 'jest-preset-angular',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/setup-jest.ts'],
  modulePaths: ['<rootDir>/src'],
  transformIgnorePatterns: [`node_modules/(?!${esModules}|ngx-markdown|marked|.*.mjs$)`],
  coverageReporters: ['html', 'text', 'text-summary', 'cobertura'],
  reporters: [
    'default',
    ['jest-junit', {outputDirectory: 'coverage', outputName: 'junit-report.xml'}]
  ]
};
