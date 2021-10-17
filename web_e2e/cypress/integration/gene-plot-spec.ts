import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GenePlotPage } from 'cypress/elements/gene-plot-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene plot tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
  });

  it('should have Affected status checkboxes', () => {
    page.getAffectedStatusCheckbox('Affected only').should('be.visible');
    page.getAffectedStatusCheckbox('Unaffected only').should('be.visible');
    page.getAffectedStatusCheckbox('Affected and unaffected').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    page.getEffectTypesCheckbox('LGDs').should('be.visible');
    page.getEffectTypesCheckbox('Missense').should('be.visible');
    page.getEffectTypesCheckbox('Synonymous').should('be.visible');
    page.getEffectTypesCheckbox('CNV+').should('be.visible');
    page.getEffectTypesCheckbox('CNV-').should('be.visible');
    page.getEffectTypesCheckbox('Other').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    page.getInheritanceTypes('Denovo').should('be.visible');
    page.getInheritanceTypes('Transmitted').should('be.visible');
  });

  it('should have variant types checkboxes', () => {
    page.getVariantTypes('del').should('be.visible');
    page.getVariantTypes('ins').should('be.visible');
    page.getVariantTypes('del').should('be.visible');
    page.getVariantTypes('CNV+').should('be.visible');
    page.getVariantTypes('CNV-').should('be.visible');
  });

  it('should have undo button', () => {
    page.undoButton.should('be.visible');
  });

  it('should have redo button', () => {
    page.redoButton.should('be.visible');
  });

  it('should have reset button', () => {
    page.resetButton.should('be.visible');
  });

  it('should have download button', () => {
    page.downloadButton.should('be.visible');
  });

  it('should have download summary button', () => {
    page.downloadSummaryButton.should('be.visible');
  });

  it('should have affected status filter field', () => {
    page.affectedStatusField.should('exist');
    page.variantsCount.should('have.text', '8 / 8');

    [['Affected only', 0], ['Unaffected only', 8], ['Affected and unaffected', 8]].forEach(element => {
      page.affectedStatusField.within(() => {
        cy.get('label').contains(element[0]).click();
      });
      page.variantsCount.should('have.text', element[1] + ' / 8');
      cy.get('label').contains(element[0]).click();
    });
  });

  it('should have effect types filter field', () => {
    page.effectTypeFiltersField.should('exist');
    page.variantsCount.should('have.text', '8 / 8');

    [['LGDs', 1], ['Missense', 8], ['Synonymous', 8], ['CNV+', 8], ['CNV-', 8], ['Other', 7]].forEach(element => {
      page.effectTypeFiltersField.within(() => {
        cy.get('span').contains(element[0]).click();
      });
      page.variantsCount.should('have.text', element[1] + ' / 8');
      cy.get('span').contains(element[0]).click();
    });
  });

  it('should have inheritance types filter field', () => {
    page.inheritanceTypesFilter.should('exist');

    [['Denovo', 0], ['Transmitted', 8]].forEach(element => {
      page.inheritanceTypesFilter.within(() => {
        cy.get('span').contains(element[0]).click();
      });
      page.variantsCount.should('have.text', element[1] + ' / 8');
      cy.get('span').contains(element[0]).click();
    });
  });

  it('should have variants types filter field', () => {
    page.variantTypesFilter.should('exist');

    [['sub', 5], ['ins', 7], ['del', 4], ['CNV+', 8], ['CNV-', 8]].forEach(element => {
      page.variantTypesFilter.within(() => {
        cy.get('label').contains(element[0]).click();
      });
      page.variantsCount.should('have.text', element[1] + ' / 8');
      cy.get('span').contains(element[0]).click();
    });
  });

  it('should contain a browser legend', () => {
    cy.scrollTo('bottom');
    ['affected', 'unaffected', 'missing-person'].forEach(element => {
      page.legend.should('contain.text', element);
    });
  });

  it('should condense introns', () => {
    cy.matchImageSnapshot('gene-plot/notCondenseIntrons.jpg');
    page.condenseIntronsCheckbox.click();
    cy.matchImageSnapshot('gene-plot/condenseIntrons.jpg');
    page.condenseIntronsCheckbox.click();
  });
});
