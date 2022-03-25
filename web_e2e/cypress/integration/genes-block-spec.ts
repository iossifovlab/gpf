import { GenesBlockPage } from "cypress/elements/genes-block-page";
import { GenotypeBrowserController } from "cypress/elements/genotype-browser-controller";
import { datasetIds, toolPageLinks } from "cypress/elements/utils";

describe('Genes block tests', () => {
  const page = new GenesBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display gene symbols panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.geneSymbolsPanel.should('not.exist');

    page.geneSymbolsButton.click();
    page.geneSymbolsPanel.should('be.visible');
  });

  it('should display error alert in gene symbols panel when the textarea is empty', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.geneSymbolsButton.click();
    page.findWarningAlertInComponent('gpf-gene-symbols').should('be.visible');

    page.geneSymbolsTextarea.type('SAMD11');
    page.findWarningAlertInComponent('gpf-gene-symbols').should('be.hidden');
  });

  it('should display gene sets panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.geneSetsPanel.should('not.exist');

    page.geneSetsButton.click();
    page.geneSetsPanel.should('be.visible');
  });

  it('should display error alert in gene sets panel when the textarea is empty', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.geneSetsButton.click();
    page.findErrorAlertInComponent('gpf-gene-sets').should('be.visible');

    page.geneSetsSearchbox.click();
    page.geneSetsSearchbox.type('non-essential genes');

    page.findGeneSetsSearchboxDropdownOptionsByText('non-essential genes').click();
    page.findErrorAlertInComponent('gpf-gene-sets').should('not.exist');
  });

  it('should display gene weights panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.genesWeightsPanel.should('not.exist');

    page.geneWeightsButton.click();
    page.genesWeightsPanel.should('be.visible');
  });
});

describe('Genes block gene sets names and count tests', () => {
  const genotypeBrowserController = new GenotypeBrowserController();
  const page = new GenesBlockPage();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome(false);
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  [
    {
      collection: 'Main',
      expectedCondition: 'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. ' +
        'Low load for disruptive mutations in autism genes and their biased transmission. PNAS (2015)'
    },
    {
      collection: 'Main',
      expectedCondition: 'autism candidates from Sanders Neuron 2015 (65): Sanders S., et. al, Insights into ' +
        'Autism Spectrum Disorder Genomic Architecture and Biology from 71 Risk Loci. Neuron (2015)'},
    {
      collection: 'Main',
      expectedCondition: 'brain critical genes (1744): Uddin M, et al. Brain-expressed exons under ' +
        'purifying selection are enriched for de novo mutations in autism spectrum disorder. Nat Genetics (2014)'
    },
    {
      collection: 'SFARI Genes',
      expectedCondition: 'sfari_all (910): SFARI Genes (2017-09): All genes'
    },
    {
      collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_1 (24): SFARI Genes (2017-09): Gene score 1'
    },
    {
      collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_2 (55): SFARI Genes (2017-09): Gene score 2'
    },
    {
      collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2016 (50): SPARK Gene list 2016'
    },
    {
      collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2017 (27): SPARK Gene list 2017'
    },
    {
      collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_all (76): SPARK Gene list ALL (2016, 2017)'
    },
    {
      collection: 'GO Terms',
      expectedCondition: 'GO:0000002 (7): mitochondrial_genome_maintenance'
    },
    {
      collection: 'GO Terms',
      expectedCondition: 'GO:0000003 (10): reproduction'
    },
    {
      collection: 'GO Terms',
      expectedCondition: 'GO:0000009 (1): alpha-1,6-mannosyltransferase_activity'
    },
    {
      collection: 'Protein domains',
      expectedCondition: '35EXO (9):'
    },
    {
      collection: 'Protein domains',
      expectedCondition: 'AAA (132):'
    },
    {
      collection: 'Protein domains',
      expectedCondition: 'ABH (18):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedCondition: 'let-7 (881):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedCondition: 'miR-101 (510):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedCondition: 'miR-124 (1018):'
    }
  ].forEach(data => {
    it('should properly display "' + data.expectedCondition + '" in "' +
      data.collection + '" collection, and the counts should match', () => {
      let actualCount;
      let expectedCount;
      let geneSetName;
      let expectedName;

      genotypeBrowserController.setStudy(datasetIds.iossifov2014);

      page.geneSetsButton.click();

      page.geneSetsSearchbox.click();

      expectedName = data.expectedCondition;
      geneSetName = expectedName.substring(0, expectedName.indexOf('(') - 1);
      genotypeBrowserController.filterGenesByGeneSets(data.collection, geneSetName);

      page.selectedGeneSet.should('contain.text', expectedName);

      page.geneSetCountElement.invoke('text').then(actualText => {
        actualCount = actualText.replace('Count: ', '').replace(' (Download)', '').trim();
        expectedCount = expectedName.substring(expectedName.indexOf('(') + 1, expectedName.indexOf(')'));
        expect(actualCount).to.eq(expectedCount);
      });

      genotypeBrowserController.filterGenesByAll();
    });
  });
});

describe('Genes block gene set file length tests', () => {
  const page = new GenesBlockPage();
  const genotypeBrowserController = new GenotypeBrowserController();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome(false);
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  [
    {
      collection: 'Main',
      expectedCondition: 'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. ' +
        'Low load for disruptive mutations in autism genes and their biased transmission. PNAS (2015)'
    },
    {
      collection: 'Main',
      expectedCondition: 'autism candidates from Sanders Neuron 2015 (65): Sanders S., et. al, Insights into ' +
        'Autism Spectrum Disorder Genomic Architecture and Biology from 71 Risk Loci. Neuron (2015)'},
    {
      collection: 'Main',
      expectedCondition: 'brain critical genes (1744): Uddin M, et al. Brain-expressed exons under ' +
        'purifying selection are enriched for de novo mutations in autism spectrum disorder. Nat Genetics (2014)'
    },
    {
      collection: 'SFARI Genes',
      expectedCondition: 'sfari_all (910): SFARI Genes (2017-09): All genes'
    },
    {
      collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_1 (24): SFARI Genes (2017-09): Gene score 1'
    },
    {
      collection: 'SFARI Genes',
      expectedCondition: 'sfari_score_2 (55): SFARI Genes (2017-09): Gene score 2'
    },
    {
      collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2016 (50): SPARK Gene list 2016'
    },
    {
      collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_2017 (27): SPARK Gene list 2017'
    },
    {
      collection: 'SPARK Gene Lists',
      expectedCondition: 'SPARK_gene_list_all (76): SPARK Gene list ALL (2016, 2017)'
    },
    {
      collection: 'GO Terms',
      expectedCondition: 'GO:0000002 (7): mitochondrial_genome_maintenance'
    },
    {
      collection: 'GO Terms',
      expectedCondition: 'GO:0000003 (10): reproduction'
    },
    {
      collection: 'GO Terms',
      expectedCondition: 'GO:0000009 (1): alpha-1,6-mannosyltransferase_activity'
    },
    {
      collection: 'Protein domains',
      expectedCondition: '35EXO (9):'
    },
    {
      collection: 'Protein domains',
      expectedCondition: 'AAA (132):'
    },
    {
      collection: 'Protein domains',
      expectedCondition: 'ABH (18):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedCondition: 'let-7 (881):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedCondition: 'miR-101 (510):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedCondition: 'miR-124 (1018):'
    }
  ].forEach(data => {
    it('should download "' + data.expectedCondition + '" in the "' + data.collection +
       '" collection and check whether the count in the name should matches ' +
       'the downloaded"s file length and the gene set"s name matches the first value of the file', () => {
      let expectedCount;
      let expectedName;
      let geneSetName;
      const downloadFilePath = Cypress.config('downloadsFolder') + '/geneset.csv';
      const results = [];

      genotypeBrowserController.setStudy(datasetIds.iossifov2014);

      page.geneSetsButton.click();
      page.geneSetsCollectionSelectorDropdownMenu.select(data.collection, {force: true});
      page.geneSetsSearchbox.click();

      results.splice(0, results.length);
      expectedName = data.expectedCondition;
      geneSetName = expectedName.substring(0, expectedName.indexOf('(') - 1);
      expectedCount = Number(expectedName.substring(expectedName.indexOf('(') + 1, expectedName.indexOf(')')));

      genotypeBrowserController.filterGenesByGeneSets(data.collection, geneSetName);
      cy.window().document().then(function (doc) {
        doc.addEventListener('click', () => {
          setTimeout(function () { doc.location.reload() }, 5000)
        })
        page.downloadButton.click();
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

describe('Genes block denovo gene set gene symbols tests', () => {
  const page = new GenesBlockPage();
  const genotypeBrowserController = new GenotypeBrowserController();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome(false);
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  [
    {
      peopleGroup: 'affected',
      expectedConditions: {
        effectTypesSearchQueries: ['LGDs', 'Missense', 'Synonymous', 'LGDs.Single', 'LGDs.Triple', 'LGDs.Male'],
        expectedGeneSymbolsFiles: [
          'cypress/fixtures/gene-sets/LGDs_iossifov_2014_status_affected.csv',
          'cypress/fixtures/gene-sets/Missense_iossifov_2014_status_affected.csv',
          'cypress/fixtures/gene-sets/Synonymous_iossifov_2014_status_affected.csv',
          'cypress/fixtures/gene-sets/LGDs_single_iossifov_2014_affected.csv',
          'cypress/fixtures/gene-sets/LGDs_triple_iossifov_2014_affected.csv',
          'cypress/fixtures/gene-sets/LGDs_male_iossifov_2014_affected.csv',
          'cypress/fixtures/gene-sets/LGDs_iossifov_2014_unaffected.csv'
        ]
      }
    },
    {
      peopleGroup: 'unaffected',
      expectedConditions: {
        effectTypesSearchQueries: ['LGDs'],
        expectedGeneSymbolsFiles: ['cypress/fixtures/gene-sets/LGDs_iossifov_2014_unaffected.csv']
      }
    }
  ].forEach(data => {
    it('should download iossifov ' + data.peopleGroup + ' denovo gene sets ' +
       'and check whether they are equal to the reference data', () => {
      const downloadedGeneSymbolsFilePath = Cypress.config('downloadsFolder') + '/geneset.csv';

      genotypeBrowserController.setStudy(datasetIds.iossifov2014);

      for (let i = 0; i < data.expectedConditions.effectTypesSearchQueries.length; i++) {
        page.geneSetsButton.click();
        page.geneSetsCollectionSelectorDropdownMenu.select('Denovo', {force: true});
        if (data.peopleGroup === 'unaffected') {
          page.findDenovoGeneSetCollectionCheckbox('iossifov_2014', 'affected').click();
          page.findDenovoGeneSetCollectionCheckbox('iossifov_2014', 'unaffected').click();
        }
        page.geneSetsSearchbox.click();
        page.geneSetsSearchbox.type(data.expectedConditions.effectTypesSearchQueries[i]);

        page.firstGeneSetFromDropdownMenu.click();
        cy.window().document().then(function (doc) {
          doc.addEventListener('click', () => {
            setTimeout(function () { doc.location.reload() }, 5000)
          })
          page.downloadButton.click();
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
