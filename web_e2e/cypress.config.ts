import { defineConfig } from 'cypress';
import { initPlugin } from '@frsource/cypress-plugin-visual-regression-diff/plugins';

export default defineConfig({
  viewportWidth: 1920,
  viewportHeight: 1080,
  defaultCommandTimeout: 5000,
  reporter: 'cypress-multi-reporters',
  reporterOptions: {
    reporterEnabled: 'spec, mocha-junit-reporter',
    mochaJunitReporterReporterOptions: {
      mochaFile: 'results/test-results/[hash].xml',
    },
  },
  downloadsFolder: 'cypress/downloads',
  screenshotsFolder: 'cypress/screenshots',
  videosFolder: 'cypress/videos',
  trashAssetsBeforeRuns: true,
  retries: {
    runMode: 2,
    openMode: 0,
  },
  env: {
    pluginVisualRegressionImagesPath: 'cypress/e2e/visual-tests/reference-images'
  },
  e2e: {
    setupNodeEvents(on, config) {
      initPlugin(on, config);
      return require('./cypress/plugins/index.js')(on, config)
    },
  }
});
