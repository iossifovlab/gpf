import { BasePage } from './utils';

export class BaseController {
  basePage = new BasePage();

  navigateToHome() {
    this.basePage.navigateToHome();
  }

  loginAdmin() {
    this.basePage.loginAdmin();
  }

  login(username: string, password: string) {
    this.basePage.login(username, password);
  }

  logout() {
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