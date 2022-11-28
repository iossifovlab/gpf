import { BasePage } from './utils';

export class ForgotPasswordPage extends BasePage {
  public get forgottenPasswordButton(): element {
    return cy.get('a').contains('Forgotten password');
  }
}
