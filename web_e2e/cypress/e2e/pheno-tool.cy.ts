import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { GeneScoresPage } from 'cypress/elements/gene-scores-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno tool tests', () => {
  const page = new PhenoToolPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    cy.deleteDownloadsFolder();
  });

  function moveSlider(which: string, dragValue: number, heightValue = 0): void {
    if (which === 'right') {
      dragValue = -dragValue;
    }
    cy.window().then(win => {
      cy.get('g[gpf-histogram-range-selector-line] > g > line').eq(which === 'left' ? 0 : 1)
        .trigger('mousedown', 0, heightValue, { // start value, height value
          view: win,
          which: 1,
          force: true,
          bubbles: true
        })
        .trigger('mousemove', dragValue, heightValue, { // how much to be dragged value, height value
          which: 1,
          force: true,
          bubbles: true
        })
        .trigger('mouseup', 0, heightValue, { // end value, height value
          which: 1,
          force: true,
          view: win,
          bubbles: true
        });
    });
  }

  it('should display genes block panel', () => {
    const genesBlockPage = new GenesBlockPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    genesBlockPage.window.should('be.visible');
  });

  it('should display pheno tool measure block panel', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolMeasurePage.block.should('be.visible');
  });

  it('should display pheno tool genotye block panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.genotypeBlockPanel.should('be.visible');
  });

  it('should display family filters block panel', () => {
    const familyFilterBlockPage = new FamilyFilterBlockPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    familyFilterBlockPage.window.should('be.visible');
  });

  it('should display "Report" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.reportButton.should('be.visible');
  });

  it('should display "Share query" button', () => {
    const saveQueryPage = new SaveQueryPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    saveQueryPage.button.should('be.visible');
  });

  it('should display "Save query" button', () => {
    const saveQueryPage = new SaveQueryPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    saveQueryPage.button.should('be.visible');
  });

  it('should display "Download" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.visible');
  });

  it('should display pheno tool results chart after "Report" button click', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.resultsChart.should('not.exist');
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    phenoToolMeasurePage.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();
    page.pressReportButton();
    page.resultsChart.should('be.visible');
  });

  it('should test "All" and "None" buttons for checkboxes of Present in Parent', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);

    page.phenoToolPresentInParent.find('button').contains('None').click();
    page.phenoToolPresentInParent.find('input[type="checkbox"]').should('not.be.checked');
    page.findErrorAlertInComponent('gpf-present-in-parent').should('be.visible');
    page.phenoToolPresentInParent.should('not.contain', 'Rarity');
    page.phenoToolPresentInParent.should('not.contain', 'ultraRare');
    page.phenoToolPresentInParent.should('not.contain', 'interval');
    page.phenoToolPresentInParent.should('not.contain', 'rare');
    page.phenoToolPresentInParent.should('not.contain', 'all');

    page.phenoToolPresentInParent.find('button').contains('All').click();
    page.phenoToolPresentInParent.find('input[type="checkbox"]').should('be.checked');
    page.findErrorAlertInComponent('gpf-present-in-parent').should('not.exist');
    page.phenoToolPresentInParent.contains('Rarity');
    page.phenoToolPresentInParent.contains('ultraRare');
    page.phenoToolPresentInParent.contains('interval');
    page.phenoToolPresentInParent.contains('rare');
    page.phenoToolPresentInParent.contains('all');
  });

  it('should test "All" and "None" buttons for checkboxes of Effect Types', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);

    page.phenoToolEffectTypes.find('button').contains('None').click();
    page.phenoToolEffectTypes.find('input[type="checkbox"]').should('not.be.checked');
    page.findErrorAlertInComponent('gpf-pheno-tool-effect-types').should('be.visible');

    page.phenoToolEffectTypes.find('button').contains('All').click();
    page.phenoToolEffectTypes.find('input[type="checkbox"]').should('be.checked');
    page.findErrorAlertInComponent('gpf-pheno-tool-effect-types').should('not.exist');
  });

  it('should test "Download" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    phenoToolMeasurePage.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.m1').click();

    const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
    const expectedVariantsPath = 'cypress/fixtures/pheno-tool/pheno_report1.csv';

    page.downloadButton.click();

    cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
      cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
        const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
        const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
        expect(downloadedFileLines).to.deep.eq(expectedFileLines);
      });
    });
  });

  [
    {id: '2', measure: 'i1.m2', normalizedBy: 'Age'},
    {id: '3', measure: 'i1.age', normalizedBy: 'Non verbal IQ'}
  ].forEach(data => {
    it(`should test check downloaded report with normalization ${data.normalizedBy}`, () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
      const phenoToolMeasurePage = new PhenoToolMeasurePage();

      phenoToolMeasurePage.searchbox.click();
      page.findButtonInComponentContainingText('gpf-pheno-measure-selector', data.measure).click();
      phenoToolMeasurePage.block.contains(data.normalizedBy).find('input[type="checkbox"]').click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      page.downloadButton.click();

      cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '4', filters: ['father only', 'mother and father', 'Nonsense', 'Nonsynonymous', 'Synonymous'] },
    {id: '5', filters: ['mother only', 'mother and father', 'neither', 'LGDs', 'Splice-site', 'Frame-shift'] }
  ].forEach(data => {
    it(`should test check downloaded report with ${data.filters.toString()}`, () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);

      const phenoToolMeasurePage = new PhenoToolMeasurePage();
      phenoToolMeasurePage.searchbox.click();
      page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.m1').click();

      page.phenoToolPresentInParent.find('button').contains('None').click();
      page.phenoToolEffectTypes.find('button').contains('None').click();

      data.filters.forEach(filter => {
        page.findButtonInComponentContainingText('gpf-pheno-tool-genotype-block', filter).click();
      });

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      page.downloadButton.click();

      cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  it('should test if buttons are enabled when there is measure', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    const saveQueryPage = new SaveQueryPage();

    phenoToolMeasurePage.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();

    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.enabled');
  });

  it('should test if buttons are disabled when there is no measure', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    const saveQueryPage = new SaveQueryPage();

    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.disabled');
  });

  it('should check if buttons are enabled when there are All and None Effect types and Present in Parent', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    const saveQueryPage = new SaveQueryPage();
    const phenoToolMeasurePage = new PhenoToolMeasurePage();

    phenoToolMeasurePage.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();

    page.phenoToolPresentInParent.find('button').contains('None').click();
    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.disabled');

    page.phenoToolPresentInParent.find('button').contains('All').click();
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.enabled');

    page.phenoToolEffectTypes.find('button').contains('None').click();
    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.disabled');

    page.phenoToolEffectTypes.find('button').contains('All').click();
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.enabled');
  });

  [
    {id: '6', familyId: 'f1' },
    {id: '7', familyId: 'f3' }
  ].forEach(data => {
    it(`should check downloaded report with family id ${data.familyId}`, () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
      const phenoToolMeasurePage = new PhenoToolMeasurePage();
      const familyPage = new FamilyFilterBlockPage();

      phenoToolMeasurePage.searchbox.click();
      page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();

      familyPage.familyIdsButton.click();
      familyPage.familyIdsTextarea.type(data.familyId);

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      page.downloadButton.click();

      cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '8', measure: 'i1.iq', borders: [100, 100]},
    {id: '9', measure: 'i1.m1', borders: [200, 150]}
  ].forEach(data => {
    it('should test advanced family filters', () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
      const phenoToolMeasurePage = new PhenoToolMeasurePage();
      const familyPage = new FamilyFilterBlockPage();

      phenoToolMeasurePage.searchbox.click();
      page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();

      familyPage.advancedButton.click();
      familyPage.searchbox.click();
      familyPage.findButtonInComponentContainingText('gpf-family-filters-block', data.measure).click();

      familyPage.histogram.should('be.visible');
      moveSlider('left', data.borders[0]);
      moveSlider('right', data.borders[1]);

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      page.downloadButton.click();

      cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
});
    });
  });

  [
    {id: '10', symbol: 'CAMSAP1' },
    {id: '11', symbol: 'SAMD11' }
  ].forEach(data => {
    it(`should check downloaded report with gene symbol ${data.symbol}`, () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
      const phenoToolMeasurePage = new PhenoToolMeasurePage();
      const genesBlockPage = new GenesBlockPage();

      page.findButtonInComponentContainingText('gpf-genes-block', 'Gene Symbols').click();
      genesBlockPage.geneSymbolsTextarea.type(data.symbol);

      phenoToolMeasurePage.searchbox.click();
      page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      page.downloadButton.click();

      cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '12', collection: 'SFARI Genes', set: 'SFARI ALL (910): SFARI Genes (2017-09): All genes', measure: 'i1.age'},
    {id: '13', collection: 'Protein domains', set: 'ANX (15):', measure: 'i1.iq' }

  ].forEach(data => {
    it('should check downloaded report with gene sets', () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
      const phenoToolMeasurePage = new PhenoToolMeasurePage();
      const genesBlockPage = new GenesBlockPage();

      genesBlockPage.geneSetsButton.click();

      genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(data.collection);
      genesBlockPage.geneSetsSearchbox.click();
      genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(data.set).click();


      phenoToolMeasurePage.searchbox.click();
      page.findButtonInComponentContainingText('gpf-pheno-measure-selector', data.measure).click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      page.downloadButton.click();

      cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {
      id: '14',
      genotype: 'comp_vcf',
      affectedStatus: 'affected',
      set: 'Missense.Male (1): Missense.Male (comp_all:status:affected;comp_vcf:status:affected)',
      measure: 'i1.age'
    },
    {
      id: '15',
      genotype: 'iossifov_2014',
      affectedStatus: 'unaffected',
      set: 'LGDs.Recurrent (3): LGDs.Recurrent (comp_all:status:affected;iossifov_2014:status:unaffected)',
      measure: 'i1.iq'
    }

  ].forEach(data => {
    it('should check downloaded report with gene set Denovo', () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
      const phenoToolMeasurePage = new PhenoToolMeasurePage();
      const genesBlockPage = new GenesBlockPage();

      genesBlockPage.geneSetsButton.click();

      genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select('Denovo');

      genesBlockPage.findGenotypeButton(data.genotype + ': Affected Status').click();
      genesBlockPage.findDenovoGeneSetCollectionCheckbox(data.genotype, data.affectedStatus).click();

      genesBlockPage.geneSetsSearchbox.click();
      genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(data.set).click();


      phenoToolMeasurePage.searchbox.click();
      page.findButtonInComponentContainingText('gpf-pheno-measure-selector', data.measure).click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      page.downloadButton.click();

      cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 5000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

});