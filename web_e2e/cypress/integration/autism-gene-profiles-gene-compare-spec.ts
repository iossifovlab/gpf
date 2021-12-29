import { AutismGeneProfilesBlock } from 'cypress/elements/autism-gene-profiles-block-page';
import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
import { sidenavPageLinks } from 'cypress/elements/utils';
import { geneData } from 'cypress/integration/autism-gene-profiles-single-view-spec';

describe('Autism gene profiles block tests', () => {
  const page = new AutismGeneProfilesBlock();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
  const autismGeneProfilesBlock = new AutismGeneProfilesBlock();
  const autismGeneProfilesSingleView = new AutismGeneProfilesSingleView();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should select multiple genes', () => {
    autismGeneProfilesTablePage.allTableRows.eq(1).click({ctrlKey:true});
    autismGeneProfilesTablePage.allTableRows.eq(3).click({ctrlKey:true});

    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► MYT1L, SPAST');

    autismGeneProfilesTablePage.allTableRows.eq(1).click({ctrlKey:true});

    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► SPAST');

  });

  it('should click dismiss gene compare button', () => {
    autismGeneProfilesTablePage.allTableRows.eq(3).click({ctrlKey:true});
    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► SPAST');

    autismGeneProfilesTablePage.allTableRows.eq(5).click({ctrlKey:true});
    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► SPAST, TBR1');

    autismGeneProfilesTablePage.legendDismissButton.click();
    autismGeneProfilesTablePage.legend.should('not.exist');
    autismGeneProfilesTablePage.legendCompareButton.should('not.exist');
    autismGeneProfilesTablePage.legendDismissButton.should('not.exist');
    autismGeneProfilesTablePage.legendSelectedGenes.should('not.exist');
  });

  it('should click compare genes button', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=**').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableRows.first().click({ctrlKey:true});

    autismGeneProfilesTablePage.geneSearchInput.clear().type('POGZ');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=**').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableRows.first().click({ctrlKey:true});

    autismGeneProfilesTablePage.legend.should('be.visible');
    autismGeneProfilesTablePage.legendCompareButton.should('be.visible');
    autismGeneProfilesTablePage.legendDismissButton.should('be.visible');
    autismGeneProfilesTablePage.legendSelectedGenes.should('have.text', '► CHD8, POGZ');

    autismGeneProfilesTablePage.legendCompareButton.click();
    autismGeneProfilesBlock.allTabs.eq(1).should('have.text', 'CHD8,POGZ×');
    autismGeneProfilesSingleView.header.eq(0).should('have.text', 'CHD8');
    autismGeneProfilesSingleView.header.eq(1).should('have.text', 'POGZ');

    autismGeneProfilesSingleView.getGeneSymbols('POGZ');
    cy.get('@geneSymbols').then(symbols => {
      expect(symbols).to.deep.equal(geneSingleViewDataPOGZ.geneSymbols, geneSingleViewDataPOGZ.geneSymbols + ' gene symbols');
    });

    const geneSingleViewDataPOGZ = geneData.find(data => data.geneSymbols === 'POGZ');
    autismGeneProfilesSingleView.getGeneSets('POGZ');
    cy.get('@geneSets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewDataPOGZ.geneSets, geneSingleViewDataPOGZ.geneSymbols + ' gene sets');
    });

    autismGeneProfilesSingleView.getDatasetData('POGZ');
    cy.get('@datasets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewDataPOGZ.datasets, geneSingleViewDataPOGZ.geneSymbols + ' single view datasets');
    });

    autismGeneProfilesSingleView.getGenomicScores('POGZ');
    cy.get('@genomicScores').then(scores => {
      expect(scores).to.deep.equal(geneSingleViewDataPOGZ.genomicScores, geneSingleViewDataPOGZ.geneSymbols + ' single view genomic scores');
    });

    autismGeneProfilesSingleView.getGeneSymbols('POGZ');
    cy.get('@geneSymbols').then(symbols => {
      expect(symbols).to.deep.equal(geneSingleViewDataPOGZ.geneSymbols, geneSingleViewDataPOGZ.geneSymbols + ' gene symbols');
    });

    const geneSingleViewDataCHD = geneData.find(data => data.geneSymbols === 'CHD8');
    autismGeneProfilesSingleView.getGeneSets('CHD8');
    cy.get('@geneSets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewDataCHD.geneSets, geneSingleViewDataCHD.geneSymbols + ' gene sets');
    });

    autismGeneProfilesSingleView.getDatasetData('CHD8');
    cy.get('@datasets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewDataCHD.datasets, geneSingleViewDataCHD.geneSymbols + ' single view datasets');
    });

    autismGeneProfilesSingleView.getGenomicScores('CHD8');
    cy.get('@genomicScores').then(scores => {
      expect(scores).to.deep.equal(geneSingleViewDataCHD.genomicScores, geneSingleViewDataCHD.geneSymbols + ' single view genomic scores');
    });

  });
});
