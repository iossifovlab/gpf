import { BasePage } from './utils';

export class RegistrationPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-registration');
  }
}
