import { BasePage } from './utils';

export class ForgotPasswordPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-forgot-password');
  }
}
