import { BasePage } from './utils';

export class AppPage extends BasePage {
  public get title(): element {
    return cy.get('#title');
  }

  public get sidenavElements(): element {
    return cy.get('div.sidenav a.nav-link');
  }
}
