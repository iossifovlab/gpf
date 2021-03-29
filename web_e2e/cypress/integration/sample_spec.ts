import { AppPage } from '../elements/sample-page';

describe('My First Test', () => {
  const appPage = new AppPage();

  it('Does not do much!', () => {
    cy.visit('http://172.18.0.4/gpf/');
    appPage.login('admin@iossifovlab.com', 'secret');
    appPage.title.should(
      'have.text',
      'GPF: Genotypes and Phenotypes in Families'
    );
  })
})