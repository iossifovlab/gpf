import { BasePage } from './utils';

export class ForgotPasswordPage extends BasePage {
  get window() {
    return cy.get('gpf-forgot-password');
  }
}
