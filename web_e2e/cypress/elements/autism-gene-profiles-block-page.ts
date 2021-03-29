import { BasePage } from './utils';

export class AutismGeneProfilesBlock extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profiles-block');
  }

  get navbar() {
    return cy.get('nav');
  }

  get allTabs() {
    return cy.get('nav li');
  }
}
