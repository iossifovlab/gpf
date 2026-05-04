const esModules = ['d3', 'd3-array', 'internmap', 'delaunator', 'robust-predicates'].join('|');

module.exports = {
  preset: 'jest-preset-angular',
  globalSetup: 'jest-preset-angular/global-setup',
  setupFilesAfterEnv: ['<rootDir>/setup-jest.ts'],
  modulePaths: ['<rootDir>/src'],
  transformIgnorePatterns: [`node_modules/(?!${esModules}|.*.mjs$)`],
  coverageReporters: ['html', 'text', 'text-summary', 'cobertura'],
  reporters: [
    'default',
    ['jest-junit', {outputDirectory: 'coverage', outputName: 'junit-report.xml'}]
  ]
};
