/// <reference types="cypress" />
/// <reference types="cypress-image-snapshot" />
// ***********************************************************
// This example plugins/index.js can be used to load plugins
//
// You can change the location of this file or turn off loading
// the plugins file with the 'pluginsFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/plugins-guide
// ***********************************************************

// This function is called when a project is opened or re-opened (e.g. due to
// the project's config changing)
const { addMatchImageSnapshotPlugin } = require('cypress-image-snapshot/plugin');
const { removeDirectory } = require('cypress-delete-downloads-folder');
const fs = require('fs');
/**
 * @type {Cypress.PluginConfig}
 */
// eslint-disable-next-line no-unused-vars
module.exports = (on, config) => {
  // `on` is used to hook into various events Cypress emits
  // `config` is the resolved Cypress config

  on('before:browser:launch', (browser = {}, launchOptions) => {
    const width = 1920;
    const height = 1080;
  
    if (browser.name === 'chrome' && browser.isHeadless) {
      launchOptions.args.push(`--window-size=${width},${height}`);
      launchOptions.args.push('--force-device-scale-factor=1');
    }
  
    if (browser.name === 'electron' && browser.isHeadless) {
      launchOptions.preferences.width = width;
      launchOptions.preferences.height = height;
    }
  
    if (browser.name === 'firefox' && browser.isHeadless) {
      launchOptions.args.push(`--width=${width}`);
      launchOptions.args.push(`--height=${height}`);
    }
  
    return launchOptions;
  })

  on('task', {
    log(message) {
      console.log(message)

      return null
    },
  });

  on('task', { removeDirectory });

  addMatchImageSnapshotPlugin(on, config);

  if (config.env.yamlPath) {
    config.env.yamlFile = fs.readFileSync(config.env.yamlPath, 'utf8');
  }

  return config;
}
