import { BasePage } from './utils';

export class BaseController {
  basePage = new BasePage();

  async navigateToHome() {
    this.basePage.navigateToHome();
  }

  async loginAdmin() {
    this.basePage.loginAdmin();
  }

  async login(username: string, password: string) {
    this.basePage.login(username, password);
  }

  async logout() {
    this.basePage.logout();
  }

  // async navigateToDatasets() {
  //   this.basePage.toggleSidenav();

  //   this.basePage.browserWaitForVisibilityOfElement(this.basePage.sidenavDatasetButton);
  //   this.basePage.sidenavManagementButton.click();
  //   this.basePage.browserWaitForVisibilityOfElement(element(by.tagName('gpf-datasets')));
  // }

  // async navigateToSavedQueries() {
  //   this.basePage.toggleSidenav();

  //   this.basePage.browserWaitForVisibilityOfElement(this.basePage.sidenavSavedQueriesButton);
  //   this.basePage.sidenavManagementButton.click();
  //   this.basePage.browserWaitForVisibilityOfElement(element(by.tagName('gpf-saved-queries')));
  // }

  // async navigateToManagement() {
  //   this.basePage.toggleSidenav();

  //   this.basePage.browserWaitForVisibilityOfElement(this.basePage.sidenavManagementButton);
  //   this.basePage.sidenavManagementButton.click();
  //   this.basePage.browserWaitForVisibilityOfElement(element(by.tagName('gpf-management')));
  // }
}