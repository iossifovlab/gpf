import { BasePage } from './utils';

export class ForgotPasswordPage extends BasePage {
  public get forgottenPasswordButton(): element {
    return cy.get('a').contains('Forgotten password');
  }

  public get inputEmailField(): element {
    return cy.get('input#id_email');
  }

  public get resetPasswordButton(): element {
    return cy.get('input').contains('Reset password');
  }
}
