import { UsersPage } from "./users_page";

export const datasetIds = {
  compAll: 'comp_all',
  compDenovo: 'comp_denovo',
  compVcf: 'comp_vcf',
  iossifov2014: 'iossifov_2014',
  multi: 'multi'
};

export const toolPageNames = {
  datasetStatistics: 'Dataset Statistics',
  genotypeBrowser: 'Genotype Browser',
  phenotypeBrowser: 'Phenotype Browser',
  phenotypeTool: 'Phenotype Tool',
  enrichmentTool: 'Enrichment Tool',
  geneBrowser: 'Gene Browser'
};

export class BasePage {
  private readonly adminUsername = 'admin@iossifovlab.com';
  private readonly adminPassword = 'secret';


  navigateToHome() {
    cy.visit('http://172.18.0.4/gpf/datasets/comp_all/commonReport');
  }

  login(username: string, password: string) {
    const usersPage = new UsersPage();

    if (!username || !password) {
      return;
    }

    usersPage.loginDropdownToggleButton.click();
    usersPage.usernameInput.type(username);
    usersPage.passwordInput.type(password);
    usersPage.loginSubmitButton.click();
  }

  loginAdmin() {
    const usersPage = new UsersPage();

    this.login(this.adminUsername, this.adminPassword);
    usersPage.loginWindow.should("not.exist");
    // cy.wait(1000);
  }

  logout() {
    const usersPage = new UsersPage();
    usersPage.logoutButton.click();
  }

  navigateToDatasetPage(dataset: string, page: string) {
    cy.get('#datasets-dropdown-menu-button').click();
    cy.get('a.dropdown-item').contains(dataset).click();
    cy.get('a.nav-link').contains(page).click();
  }
}
