import { BasePage } from './utils';

export class AutismGeneProfilesBlock extends BasePage {
  public get window(): element {
    return cy.get('gpf-autism-gene-profiles-block');
  }

  public get navbar(): element {
    return cy.get('nav');
  }

  public get allTabs() : element {
    return cy.get('nav li');
  }

  public get homeTab(): element {
    return cy.get('nav li').first();
  }

  public get keybindIcon(): element {
    return cy.get('.keybinds-icon span');
  }

  public get keybindTooltip(): element {
    return cy.get('.keybinds-tooltip');
  }
}
