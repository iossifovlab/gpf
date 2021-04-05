import { ErrorsAlertPage } from "cypress/elements/errors-alert-page";
import { GenesBlockPage } from "cypress/elements/genes-block-page";
import { GenotypeBrowserController } from "cypress/elements/genotype-browser-controller";
import { datasetIds, toolPageNames } from "cypress/elements/utils";

describe('Genes block panel tests', () => {
  const genesBlockPage = new GenesBlockPage();

  before(() => {
    genesBlockPage.navigateToHome();
    genesBlockPage.loginAdmin();
  });

  after(() => {
    genesBlockPage.logout();
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid');
    genesBlockPage.navigateToHome();
  });

  it('should display gene symbols panel', () => {
    genesBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genesBlockPage.geneSymbolsPanel.should('not.exist');

    genesBlockPage.geneSymbolsButton.click();
    genesBlockPage.geneSymbolsPanel.should('be.visible');
  });

  it('should display error alert in gene symbols panel when the textarea is empty', () => {
    const errorsAlertPage = new ErrorsAlertPage();

    genesBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genesBlockPage.geneSymbolsButton.click();
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-symbols').should('be.visible');

    genesBlockPage.geneSymbolsTextarea.type('SAMD11');
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-symbols').should('not.exist');
  });

  it('should display gene sets panel', () => {
    genesBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genesBlockPage.geneSetsPanel.should('not.exist');

    genesBlockPage.geneSetsButton.click();
    genesBlockPage.geneSetsPanel.should('be.visible');
  });

  it('should display error alert in gene sets panel when the textarea is empty', () => {
    const errorsAlertPage = new ErrorsAlertPage();

    genesBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genesBlockPage.geneSetsButton.click();
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-sets').should('be.visible');

    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type('non-essential genes');

    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText('non-essential genes').click();
    errorsAlertPage.findAlertWindowInComponent('gpf-gene-sets').should('not.exist');
  });

  it('should display gene weights panel', () => {
    genesBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genesBlockPage.genesWeightsPanel.should('not.exist');

    genesBlockPage.geneWeightsButton.click();
    genesBlockPage.genesWeightsPanel.should('be.visible');
  });
});

describe('Gene sets names and count tests', () => {
  const genotypeBrowserController = new GenotypeBrowserController();
  const genesBlockPage = new GenesBlockPage();

  before(() => {
    genotypeBrowserController.navigateToHome();
    genotypeBrowserController.loginAdmin();
  });

  after(() => {
    genotypeBrowserController.logout();
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid');
    genotypeBrowserController.navigateToHome();
  });

  [{ collection: 'Main',
      expectedCondition: 'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. Low load for disruptive ' +
      'mutations in autism genes and their biased transmission. PNAS (2015)'},
    { collection: 'Main',
      expectedCondition: 'autism candidates from Sanders Neuron 2015 (65): Sanders S., et. al, Insights into Autism Spectrum ' +
      'Disorder Genomic Architecture and Biology from 71 Risk Loci. Neuron (2015)'},
    { collection: 'Main',
      expectedCondition: 'brain critical genes (1744): Uddin M, et al. Brain-expressed exons under purifying selection are ' +
      'enriched for de novo mutations in autism spectrum disorder. Nat Genetics (2014)'},
    { collection: 'SFARI Genes',
      expectedCondition: 'sfari_all (910): SFARI Genes (2017-09): All genes'},
    { collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_1 (24): SFARI Genes (2017-09): Gene score 1'},
    { collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_2 (55): SFARI Genes (2017-09): Gene score 2'},
    { collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2016 (50): SPARK Gene list 2016'},
    { collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2017 (27): SPARK Gene list 2017'},
    { collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_all (76): SPARK Gene list ALL (2016, 2017)'},
    { collection: 'GO Terms',
      expectedCondition: 'GO:0000002 (7): mitochondrial_genome_maintenance'},
    { collection: 'GO Terms',
      expectedCondition: 'GO:0000003 (10): reproduction'},
    { collection: 'GO Terms',
      expectedCondition: 'GO:0000009 (1): alpha-1,6-mannosyltransferase_activity'},
    { collection: 'Protein domains',
      expectedCondition: '35EXO (9):'},
    { collection: 'Protein domains',
      expectedCondition: 'AAA (132):'},
    { collection: 'Protein domains',
      expectedCondition: 'ABH (18):'},
    { collection: 'miRNA from Darnell',
      expectedCondition: 'let-7 (881):'},
    { collection: 'miRNA from Darnell',
      expectedCondition: 'miR-101 (510):'},
    { collection: 'miRNA from Darnell',
      expectedCondition: 'miR-124 (1018):'}
  ].forEach((data) => {
    it('should properly display \'' + data.expectedCondition + '\' in \'' + data.collection + '\' collection, and the counts should match', () => {
      let actualCount;
      let expectedCount;
      let geneSetName;
      let expectedName;

      genotypeBrowserController.setStudy(datasetIds.iossifov2014);

      genesBlockPage.geneSetsButton.click();

      genesBlockPage.geneSetsSearchbox.click();

      expectedName = data.expectedCondition;
      geneSetName = expectedName.substring(0, expectedName.indexOf('(') - 1);
      genotypeBrowserController.filterGenesByGeneSets(data.collection, geneSetName);

      genesBlockPage.selectedGeneSet.should('contain.text', expectedName);

      genesBlockPage.geneSetCountElement.invoke('text').then(actualText => {
        actualCount = actualText.replace('Count: ', '').replace(' (Download)', '').trim();
        expectedCount = expectedName.substring(expectedName.indexOf('(') + 1, expectedName.indexOf(')'));
        expect(actualCount).to.eq(expectedCount);
      });

      genotypeBrowserController.filterGenesByAll();
    });
  });
});

describe('Gene set file length tests', () => {
  const genesBlockPage = new GenesBlockPage();
  const genotypeBrowserController = new GenotypeBrowserController();

  before(() => {
    genotypeBrowserController.navigateToHome();
    genotypeBrowserController.loginAdmin();
  });

  after(() => {
    genotypeBrowserController.logout();
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid');
    genotypeBrowserController.navigateToHome();
  });

  [{ collection: 'Main',
      expectedCondition: 'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. Low load for disruptive ' +
      'mutations in autism genes and their biased transmission. PNAS (2015)'},
    { collection: 'Main',
      expectedCondition: 'autism candidates from Sanders Neuron 2015 (65): Sanders S., et. al, Insights into Autism Spectrum ' +
      'Disorder Genomic Architecture and Biology from 71 Risk Loci. Neuron (2015)'},
    { collection: 'Main',
      expectedCondition: 'brain critical genes (1744): Uddin M, et al. Brain-expressed exons under purifying selection are ' +
      'enriched for de novo mutations in autism spectrum disorder. Nat Genetics (2014)'},
    { collection: 'SFARI Genes',
      expectedCondition: 'sfari_all (910): SFARI Genes (2017-09): All genes'},
    { collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_1 (24): SFARI Genes (2017-09): Gene score 1'},
    { collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_2 (55): SFARI Genes (2017-09): Gene score 2'},
    { collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2016 (50): SPARK Gene list 2016'},
    { collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2017 (27): SPARK Gene list 2017'},
    { collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_all (76): SPARK Gene list ALL (2016, 2017)'},
    { collection: 'GO Terms',
      expectedCondition: 'GO:0000002 (7): mitochondrial_genome_maintenance'},
    { collection: 'GO Terms',
      expectedCondition: 'GO:0000003 (10): reproduction'},
    { collection: 'GO Terms',
      expectedCondition: 'GO:0000009 (1): alpha-1,6-mannosyltransferase_activity'},
    { collection: 'Protein domains',
      expectedCondition: '35EXO (9):'},
    { collection: 'Protein domains',
      expectedCondition: 'AAA (132):'},
    { collection: 'Protein domains',
      expectedCondition: 'ABH (18):'},
    { collection: 'miRNA from Darnell',
      expectedCondition: 'let-7 (881):'},
    { collection: 'miRNA from Darnell',
      expectedCondition: 'miR-101 (510):'},
    { collection: 'miRNA from Darnell',
      expectedCondition: 'miR-124 (1018):'}
  ].forEach((data) => {
    it('should download \'' + data.expectedCondition + '\' in the \'' + data.collection + '\' collection and check whether the count in the name should matches ' +
      'the downloaded\'s file length and the gene set\'s name matches the first value of the file', () => {
      let expectedCount;
      let expectedName;
      let geneSetName;
      const downloadFilePath = Cypress.config('downloadsFolder') + '/geneset.csv';
      const results = [];

      genotypeBrowserController.setStudy(datasetIds.iossifov2014);

      genesBlockPage.geneSetsButton.click();
      genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(data.collection);
      genesBlockPage.geneSetsSearchbox.click();

      results.splice(0, results.length);
      expectedName = data.expectedCondition;
      geneSetName = expectedName.substring(0, expectedName.indexOf('(') - 1);
      expectedCount = Number(expectedName.substring(expectedName.indexOf('(') + 1, expectedName.indexOf(')')));

      genotypeBrowserController.filterGenesByGeneSets(data.collection, geneSetName);
      cy.window().document().then(function (doc) {
        doc.addEventListener('click', () => {
          setTimeout(function () { doc.location.reload() }, 5000)
        })
        genesBlockPage.downloadButton.click();
      });

      cy.readFile(downloadFilePath, { timeout: 5000 }).then(text => {
        const textLines = text.split(/\r\n|\r|\n/);
        expect(textLines.length - 2).to.eq(expectedCount);
        expectedName = expectedName.replace(/\s*\(\d+\)\s*/, '');
        expect(textLines[0].replace(/^"(.*)"$/, '$1').trim()).to.eq(expectedName);
      });

      genotypeBrowserController.filterGenesByAll();
    });
  });
});

describe('Denovo gene set gene symbols tests', () => {
  const genesBlockPage = new GenesBlockPage();
  const genotypeBrowserController = new GenotypeBrowserController();

  before(() => {
    genotypeBrowserController.navigateToHome();
    genotypeBrowserController.loginAdmin();
  });

  after(() => {
    genotypeBrowserController.logout();
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid');
    genotypeBrowserController.navigateToHome();
  });

  [{peopleGroup: 'affected',
    expectedConditions: {
    effectTypesSearchQueries: ['LGDs', 'Missense', 'Synonymous', 'LGDs.Single', 'LGDs.Triple', 'LGDs.Male'],
    expectedGeneSymbolsFiles: [
      'cypress/fixtures/gene_sets/LGDs_iossifov_2014_status_affected.csv', 'cypress/fixtures/gene_sets/Missense_iossifov_2014_status_affected.csv',
      'cypress/fixtures/gene_sets/Synonymous_iossifov_2014_status_affected.csv', 'cypress/fixtures/gene_sets/LGDs_single_iossifov_2014_affected.csv',
      'cypress/fixtures/gene_sets/LGDs_triple_iossifov_2014_affected.csv', 'cypress/fixtures/gene_sets/LGDs_male_iossifov_2014_affected.csv',
      'cypress/fixtures/gene_sets/LGDs_iossifov_2014_unaffected.csv'
    ]}},
    {peopleGroup: 'unaffected',
    expectedConditions: {
    effectTypesSearchQueries: ['LGDs'],
    expectedGeneSymbolsFiles: ['cypress/fixtures/gene_sets/LGDs_iossifov_2014_unaffected.csv']}}
  ].forEach((data) => {
    it('should download iossifov ' + data.peopleGroup + ' denovo gene sets ' +
       'and check whether they are equal to the reference data', () => {
      const downloadedGeneSymbolsFilePath = Cypress.config('downloadsFolder') + '/geneset.csv';

      genotypeBrowserController.setStudy(datasetIds.iossifov2014);

      for (let i = 0; i < data.expectedConditions.effectTypesSearchQueries.length; i++) {
        genesBlockPage.geneSetsButton.click();
        genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select('Denovo');
        if (data.peopleGroup === 'unaffected') {
          genesBlockPage.findDenovoGeneSetCollectionCheckbox('iossifov_2014', 'affected').click();
          genesBlockPage.findDenovoGeneSetCollectionCheckbox('iossifov_2014', 'unaffected').click();
        }
        genesBlockPage.geneSetsSearchbox.click();
        genesBlockPage.geneSetsSearchbox.type(data.expectedConditions.effectTypesSearchQueries[i]);

        genesBlockPage.getFirstGeneSetFromDropdownMenu().click();
        cy.window().document().then(function (doc) {
          doc.addEventListener('click', () => {
            setTimeout(function () { doc.location.reload() }, 5000)
          })
          genesBlockPage.downloadButton.click();
        });

        cy.readFile(downloadedGeneSymbolsFilePath, { timeout: 5000 }).then(text => {
          const textLines = text.split(/\r\n|\r|\n/);
          cy.readFile(data.expectedConditions.expectedGeneSymbolsFiles[i], { timeout: 5000 }).then(expectedText => {
            const expectedTextLines = expectedText.split(/\r\n|\r|\n/);
            expect(textLines.slice(1).sort()).to.deep.eq(expectedTextLines.slice(1).sort());
          });
        });
      }
    });
  });
});
