const esModules = ['d3', 'd3-array', 'internmap', 'delaunator', 'robust-predicates'].join('|');

module.exports = {
  preset: 'jest-preset-angular',
  globalSetup: 'jest-preset-angular/global-setup',
  modulePaths: ['<rootDir>/src'],
  transformIgnorePatterns: [`node_modules/(?!${esModules})`]
};
