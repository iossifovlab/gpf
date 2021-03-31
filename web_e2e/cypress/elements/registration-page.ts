import { BasePage } from './utils';

export class RegistrationPage extends BasePage {
  get window() {
    return cy.get('gpf-registration');
  }
}
