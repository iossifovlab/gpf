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
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    cy.deleteDownloadsFolder();
  });

  it('should display genes block panel', () => {
    const genesBlockPage = new GenesBlockPage();
    genesBlockPage.window.should('be.visible');
  });

  it('should display pheno tool measure block panel', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    phenoToolMeasurePage.block.should('be.visible');
  });

  it('should display pheno tool genotype block panel', () => {
    page.genotypeBlockPanel.should('be.visible');
  });

  it('should display family filters block panel', () => {
    const familyFilterBlockPage = new FamilyFilterBlockPage();
    familyFilterBlockPage.window.should('be.visible');
  });

  it('should display "Report" button', () => {
    page.reportButton.should('be.visible');
  });

  it('should display "Share/save query" button', () => {
    const saveQueryPage = new SaveQueryPage();
    saveQueryPage.button.should('be.visible');
  });

  it('should display "Save query" button', () => {
    const saveQueryPage = new SaveQueryPage();
    saveQueryPage.button.should('be.visible');
  });

  it('should display "Download" button', () => {
    page.downloadButton.should('be.visible');
  });

  it('should display pheno tool results chart after "Report" button click', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();

    page.resultsChart.should('not.exist');
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    phenoToolMeasurePage.searchbox.click();
    phenoToolMeasurePage.getDropdownOptionByText('i1.age').click();
    page.pressReportButton();
    page.resultsChart.should('be.visible');
  });

  it('should hide pheno tool results chart on state change', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();

    page.resultsChart.should('not.exist');

    phenoToolMeasurePage.searchbox.click();
    phenoToolMeasurePage.getDropdownOptionByText('i1.age').click();
    page.pressReportButton();
    page.resultsChart.should('be.visible');

    page.effectTypes.find('button').contains('None').click();
    page.resultsChart.should('not.exist');
  });

  it('should proplery disable the "Report", "Save/share query" and "Download" buttons on errors', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    const saveQueryPage = new SaveQueryPage();
    const familyPage = new FamilyFilterBlockPage();

    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.downloadButton.should('be.disabled');

    phenoToolMeasurePage.searchbox.click();
    phenoToolMeasurePage.getDropdownOptionByText('i1.age').click();
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.downloadButton.should('be.enabled');

    phenoToolMeasurePage.clearMeasureButton.click();
    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.downloadButton.should('be.disabled');

    phenoToolMeasurePage.searchbox.click();
    phenoToolMeasurePage.getDropdownOptionByText('i1.age').click();
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.downloadButton.should('be.enabled');
    page.presentInParent.find('button').contains('None').click();
    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.downloadButton.should('be.disabled');

    page.presentInParent.find('button').contains('All').click();
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.downloadButton.should('be.enabled');

    page.effectTypes.find('button').contains('None').click();
    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.downloadButton.should('be.disabled');
    page.effectTypes.find('button').contains('All').click();
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.downloadButton.should('be.enabled');

    familyPage.familyIdsButton.click();
    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.downloadButton.should('be.disabled');

    familyPage.familyIdsTextarea.type('f1');
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.downloadButton.should('be.enabled');

    familyPage.advancedButton.click();
    saveQueryPage.button.should('be.disabled');
    page.reportButton.should('be.disabled');
    page.downloadButton.should('be.disabled');
    familyPage.searchbox.click();
    familyPage.getDropdownMenuOptionByText('i1.age').click();
    saveQueryPage.button.should('be.enabled');
    page.reportButton.should('be.enabled');
    page.downloadButton.should('be.enabled');
  });
});

describe('Pheno tool download tests', () => {
  const page = new PhenoToolPage();
  const phenoToolMeasurePage = new PhenoToolMeasurePage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    cy.deleteDownloadsFolder();
  });

  it('should download i1.m1 and check if it equals the reference data', () => {
    phenoToolMeasurePage.searchbox.click();
    phenoToolMeasurePage.getDropdownOptionByText('i1.m1').click();

    const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
    const expectedVariantsPath = 'cypress/fixtures/pheno-tool/pheno_report1.csv';

    cy.window().document().then(doc => {
      doc.addEventListener('click', () => {
        setTimeout(() => doc.location?.reload(), 20000);
      });
      page.downloadButton.click();
    });

    cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
      cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
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
    it(`should normalize by "${data.normalizedBy}", download report and compare it to the reference data`, () => {
      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText(data.measure).click();
      phenoToolMeasurePage.block.contains(data.normalizedBy).find('input[type="checkbox"]').click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
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
    it(`should apply ${data.filters.toString()} filters, download report and compare it to the reference data`, () => {
      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText('i1.m1').click();

      page.presentInParent.find('button').contains('None').click();
      page.effectTypes.find('button').contains('None').click();

      data.filters.forEach(filter => {
        page.findButtonInComponentContainingText('gpf-pheno-tool-genotype-block', filter).click();
      });

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '6', familyId: 'f1'},
    {id: '7', familyId: 'f3'}
  ].forEach(data => {
    it(`should check downloaded report with family id ${data.familyId}`, () => {
      const familyPage = new FamilyFilterBlockPage();

      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText('i1.age').click();

      familyPage.familyIdsButton.click();
      familyPage.familyIdsTextarea.type(data.familyId);

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '8', measure: 'i1.iq', familyHistogramfromTo: ['33', '130']},
    {id: '9', measure: 'i1.m1', familyHistogramfromTo: ['84', '107']}
  ].forEach(data => {
    it('should test advanced family filters', () => {
      const familyPage = new FamilyFilterBlockPage();
      cy.intercept('POST', '/gpf/api/v3/measures/partitions').as('partitions');

      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText('i1.age').click();

      familyPage.advancedButton.click();
      familyPage.searchbox.click();
      familyPage.getDropdownMenuOptionByText(data.measure).click();

      familyPage.histogram.should('be.visible');
      familyPage.fromInputField.clear();
      familyPage.fromInputField.type(data.familyHistogramfromTo[0]);
      familyPage.toInputField.clear();
      familyPage.toInputField.type(data.familyHistogramfromTo[1]);
      cy.wait(3000); // wait needed for https://github.com/iossifovlab/gpfjs/issues/844

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.wait('@partitions');
      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '10', geneSymbol: 'CAMSAP1'},
    {id: '11', geneSymbol: 'SAMD11'}
  ].forEach(data => {
    it(`should check downloaded report with gene symbol ${data.geneSymbol}`, () => {
      const genesBlockPage = new GenesBlockPage();

      genesBlockPage.geneSymbolsButton.click();
      genesBlockPage.geneSymbolsTextarea.type(data.geneSymbol);

      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText('i1.age').click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '12', collection: 'SFARI Genes', set: 'SFARI ALL (910): SFARI Genes (2017-09): All genes', measure: 'i1.age'},
    {id: '13', collection: 'Protein domains', set: 'AMOP (3): ', measure: 'i1.iq'}
  ].forEach(data => {
    it('should check downloaded report with gene sets', () => {
      const genesBlockPage = new GenesBlockPage();

      genesBlockPage.geneSetsButton.click();

      genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(data.collection);
      genesBlockPage.geneSetsSearchbox.click();
      genesBlockPage.geneSetsSearchbox.type(data.set.substring(0, data.set.indexOf(' (')));
      genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(data.set).click();

      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText(data.measure).click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
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
      const genesBlockPage = new GenesBlockPage();

      genesBlockPage.geneSetsButton.click();

      genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select('Denovo');

      genesBlockPage.findDenovoGeneSetsAccordionButtonByText(data.genotype + ': Affected Status').click();
      genesBlockPage.findDenovoGeneSetCollectionCheckbox(data.genotype, data.affectedStatus).click();

      genesBlockPage.geneSetsSearchbox.click();
      genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(data.set).click();

      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText(data.measure).click();

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });

  [
    {id: '16', measure: 'i1.age', geneScore: 'LGD rank', geneScoresHistogramFromTo: ['2944', '14716']},
    {id: '17', measure: 'i1.m1', geneScore: 'ExAC pRec', geneScoresHistogramFromTo: ['0.000012', '0.832']}
  ].forEach(data => {
    it(`should check downloaded report with gene score ${data.geneScore}`, () => {
      const genesBlockPage = new GenesBlockPage();
      const geneScoresPage = new GeneScoresPage();
      cy.intercept('POST', '/gpf/api/v3/gene_scores/partitions').as('partitions');

      genesBlockPage.geneScoresButton.click();

      geneScoresPage.dropdownButton.select(data.geneScore);

      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText(data.measure).click();

      phenoToolMeasurePage.fromInputField.clear();
      phenoToolMeasurePage.fromInputField.type(data.geneScoresHistogramFromTo[0]);
      phenoToolMeasurePage.toInputField.clear();
      phenoToolMeasurePage.toInputField.type(data.geneScoresHistogramFromTo[1]);

      const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/pheno_report.csv';
      const expectedVariantsPath = `cypress/fixtures/pheno-tool/pheno_report${data.id}.csv`;

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadButton.click();
      });

      cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });
});
