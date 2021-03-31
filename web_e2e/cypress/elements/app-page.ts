import { BasePage } from './utils';

export class AppPage extends BasePage {
  get title() {
    return cy.get('#title');
  }

  get sidenavElements() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a.nav-link');
  }
}
