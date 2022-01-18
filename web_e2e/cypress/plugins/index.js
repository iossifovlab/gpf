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
const fs = require('fs');
/**
 * @type {Cypress.PluginConfig}
 */
// eslint-disable-next-line no-unused-vars
module.exports = (on, config) => {
  // `on` is used to hook into various events Cypress emits
  // `config` is the resolved Cypress config

  addMatchImageSnapshotPlugin(on, config);

  config.env.yamlFile = fs.readFileSync('/home/joan/gpf-e2e/cypress/iossifov.data.expected.yaml', 'utf8');

  return config;
}
