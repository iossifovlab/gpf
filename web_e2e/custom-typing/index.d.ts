export {};

declare global {
  type element = Cypress.Chainable<JQuery<HTMLElement>>;
}
