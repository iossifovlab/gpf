import { BasePage } from './utils';

export class AutismGeneProfilesBlock extends BasePage {
  public get window(): element {
    return cy.get('gpf-autism-gene-profiles-block');
  }

  public get keybindIcon(): element {
    return cy.get('#keybinds-icon');
  }

  public get keybindTooltip(): element {
    return cy.get('.keybinds-tooltip');
  }
}
