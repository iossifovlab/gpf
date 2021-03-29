import { BasePage } from "./utils";

export class ErrorsAlertPage extends BasePage {
  findAlertWindowInComponent(componentSelector: string) {
    return cy.get(`${componentSelector} gpf-errors-alert .alert-danger`);
    // return cy.get(componentSelector).get('gpf-errors-alert').get('.alert-danger');
  }
}
