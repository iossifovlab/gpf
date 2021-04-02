import { ErrorsAlertPage } from "cypress/elements/errors-alert-page";
import { GenesBlockPage } from "cypress/elements/genes-block-page";
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

// describe('Gene sets names and count tests', () => {
//   const genotypeBrowserController = new GenotypeBrowserController();
//   const genesBlockPage = new GenesBlockPage();

//   beforeAll(() => {
//     browser.restart();
//     browser.waitForAngularEnabled(false);
//     genotypeBrowserController.navigateToHome();
//     genotypeBrowserController.loginAdmin();
//   });

//   afterAll(() => {
//     genotypeBrowserController.logout();
//   });

//   beforeEach(() => {
//     genotypeBrowserController.navigateToHome();
//   });

//   using([
//     {collection: 'Main', expectedConditions: {text: [
//       'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. Low load for disruptive ' +
//         'mutations in autism genes and their biased transmission. PNAS (2015)',
//       'autism candidates from Sanders Neuron 2015 (65): Sanders S., et. al, Insights into Autism Spectrum ' +
//         'Disorder Genomic Architecture and Biology from 71 Risk Loci. Neuron (2015)',
//       'brain critical genes (1744): Uddin M, et al. Brain-expressed exons under purifying selection are ' +
//         'enriched for de novo mutations in autism spectrum disorder. Nat Genetics (2014)'
//     ]}},
//     {collection: 'SFARI Genes', expectedConditions: {text: [
//       'sfari_all (910): SFARI Genes (2017-09): All genes',
//       'sfari_score_1 (24): SFARI Genes (2017-09): Gene score 1',
//       'sfari_score_2 (55): SFARI Genes (2017-09): Gene score 2'
//     ]}},
//     {collection: 'SPARK Gene Lists', expectedConditions: {text: [
//       'SPARK_gene_list_2016 (50): SPARK Gene list 2016',
//       'SPARK_gene_list_2017 (27): SPARK Gene list 2017',
//       'SPARK_gene_list_all (76): SPARK Gene list ALL (2016, 2017)'
//     ]}},
//     {collection: 'GO Terms', expectedConditions: {text: [
//       'GO:0000002 (7): mitochondrial_genome_maintenance',
//       'GO:0000003 (10): reproduction',
//       'GO:0000009 (1): alpha-1,6-mannosyltransferase_activity'
//     ]}},
//     {collection: 'Protein domains', expectedConditions: {text: [
//       '35EXO (9):', 'AAA (132):', 'ABH (18):'
//     ]}},
//     {collection: 'miRNA from Darnell', expectedConditions: {text: [
//       'let-7 (881):', 'miR-101 (510):', 'miR-124 (1018):'
//     ]}},
//   ], (data) => {
//     it('should properly display the gene sets in \'' + data.collection + '\' collection, and the counts should match', () => {
//       let actualCount;
//       let expectedCount;
//       let geneSetName;
//       let expectedName;

//       genotypeBrowserController.setStudy(datasetIds.iossifov2014);

//       genesBlockPage.geneSetsButton.click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.geneSetsPanel);

//       genesBlockPage.geneSetsCollectionSelectorDropdownMenu.click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.findGeneSetsCollectionOptionByText(data.collection));
//       genesBlockPage.findGeneSetsCollectionOptionByText(data.collection).click();

//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.geneSetsPanel);
//       genesBlockPage.geneSetsSearchbox.click();

//       for (let i = 0; i < data.expectedConditions.text.length; i++) {
//         expectedName = data.expectedConditions.text[i];
//         geneSetName = expectedName.substring(0, expectedName.indexOf('(') - 1);
//         genotypeBrowserController.filterGenesByGeneSets(data.collection, geneSetName);

//         expect(genesBlockPage.selectedGeneSet.getText()).toBe(expectedName);

//         actualCount = genesBlockPage.geneSetCountElement.getText();
//         expectedCount = expectedName.substring(expectedName.indexOf('(') + 1, expectedName.indexOf(')'));
//         expect((actualCount).replace('Count: ', '').replace(' (Download)', '')).toBe(expectedCount);

//         genotypeBrowserController.filterGenesByAll();
//       }
//     });
//   });
// });

// describe('Gene set file length tests', () => {
//   const genesBlockPage = new GenesBlockPage();
//   const genotypeBrowserController = new GenotypeBrowserController();

//   beforeAll(() => {
//     genesBlockPage.prepareBrowser();
//     genotypeBrowserController.navigateToHome();
//     genotypeBrowserController.loginAdmin();

//   });

//   afterAll(() => {
//     genotypeBrowserController.logout();
//   });

//   beforeEach(() => {
//     genotypeBrowserController.navigateToHome();
//   });

//   using([
//     {collection: 'Main', expectedConditions: {text: [
//       'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. Low load for disruptive ' +
//         'mutations in autism genes and their biased transmission. PNAS (2015)',
//       'autism candidates from Sanders Neuron 2015 (65): Sanders S., et. al, Insights into Autism Spectrum ' +
//         'Disorder Genomic Architecture and Biology from 71 Risk Loci. Neuron (2015)',
//       'brain critical genes (1744): Uddin M, et al. Brain-expressed exons under purifying selection are ' +
//         'enriched for de novo mutations in autism spectrum disorder. Nat Genetics (2014)'
//     ]}},
//     {collection: 'SFARI Genes', expectedConditions: {text: [
//       'sfari_all (910): SFARI Genes (2017-09): All genes',
//       'sfari_score_1 (24): SFARI Genes (2017-09): Gene score 1',
//       'sfari_score_2 (55): SFARI Genes (2017-09): Gene score 2'
//     ]}},
//     {collection: 'SPARK Gene Lists', expectedConditions: {text: [
//       'SPARK_gene_list_2016 (50): SPARK Gene list 2016',
//       'SPARK_gene_list_2017 (27): SPARK Gene list 2017',
//       'SPARK_gene_list_all (76): SPARK Gene list ALL (2016, 2017)'
//     ]}},
//     {collection: 'GO Terms', expectedConditions: {text: [
//       'GO:0000002 (7): mitochondrial_genome_maintenance',
//       'GO:0000003 (10): reproduction',
//       'GO:0000009 (1): alpha-1,6-mannosyltransferase_activity'
//     ]}},
//     {collection: 'Protein domains', expectedConditions: {text: [
//       '35EXO (9):', 'AAA (132):', 'ABH (18):'
//     ]}},
//     {collection: 'miRNA from Darnell', expectedConditions: {text: [
//       'let-7 (881):', 'miR-101 (510):', 'miR-124 (1018):'
//     ]}},
//   ], (data) => {
//     it('should download gene sets in the \'' + data.collection + '\' collection and check whether the count in the name should matches ' +
//        'the downloaded\'s file length and the gene set\'s name matches the first value of the file', () => {
//       let expectedCount;
//       let expectedName;
//       let geneSetName;
//       const filename = browser.params.genesetsDownloadPath + browser.params.genesetsFileName;
//       const results = [];

//       if (!fs.existsSync(browser.params.genesetsDownloadPath)) {
//         fs.mkdirSync(browser.params.genesetsDownloadPath);
//       }

//       if (fs.existsSync(filename)) {
//         fs.unlinkSync(filename);
//       }

//       genotypeBrowserController.setStudy(datasetIds.iossifov2014);

//       genesBlockPage.geneSetsButton.click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.geneSetsPanel);
//       genesBlockPage.geneSetsCollectionSelectorDropdownMenu.click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.findGeneSetsCollectionOptionByText(data.collection));
//       genesBlockPage.findGeneSetsCollectionOptionByText(data.collection).click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.geneSetsPanel);
//       genesBlockPage.geneSetsSearchbox.click();
//       for (let i = 0; i < data.expectedConditions.text.length; i++) {
//         results.splice(0, results.length);
//         expectedName = data.expectedConditions.text[i];
//         geneSetName = expectedName.substring(0, expectedName.indexOf('(') - 1);
//         expectedCount = Number(expectedName.substring(expectedName.indexOf('(') + 1, expectedName.indexOf(')')));

//         genotypeBrowserController.filterGenesByGeneSets(data.collection, geneSetName);

//         genesBlockPage.downloadButton.click();
//         browser.driver.wait(() => {
//           return fs.existsSync(filename);
//         }, 30000);
//         new Promise<void>((resolve) => {
//           fs.createReadStream(filename)
//           .pipe(csv())
//           .on('data', (d) => results.push(d))
//           .on('end', () => {
//             expect(results.length).toBe(expectedCount);
//             expectedName = expectedName.replace(/\s*\(\d+\)\s*/, '');
//             expect(Object.keys(results[0])[0].trim()).toBe(expectedName);
//             fs.unlinkSync(filename);
//             resolve();
//           });
//         });
//         genotypeBrowserController.filterGenesByAll();
//       }
//     });
//   });
// });

// describe('Denovo gene set gene symbols tests', () => {
//   const genesBlockPage = new GenesBlockPage();
//   const genotypeBrowserController = new GenotypeBrowserController();

//   beforeAll(() => {
//     genesBlockPage.prepareBrowser();
//     genotypeBrowserController.navigateToHome();
//     genotypeBrowserController.loginAdmin();
//   });

//   afterAll(() => {
//     genotypeBrowserController.logout();
//   });

//   beforeEach(() => {
//     genotypeBrowserController.navigateToHome();
//   });

//   function areSetsEqual(leftSet, rightSet) {
//     if (leftSet.size !== rightSet.size) {
//       return false;
//     }
//     for (const entry of leftSet) {
//       if (!rightSet.has(entry)) {
//         return false;
//       }
//     }
//     return true;
//   }

//   using([
//     {
//       peopleGroup: 'affected',
//       expectedConditions: {
//         effectTypesSearchQueries: ['LGDs', 'Missense', 'Synonymous', 'LGDs.Single', 'LGDs.Triple', 'LGDs.Male'],
//         expectedGeneSymbolsFiles: [
//           'gene_sets/LGDs_iossifov_2014_status_affected.csv', 'gene_sets/Missense_iossifov_2014_status_affected.csv',
//           'gene_sets/Synonymous_iossifov_2014_status_affected.csv', 'gene_sets/LGDs_single_iossifov_2014_affected.csv',
//           'gene_sets/LGDs_triple_iossifov_2014_affected.csv', 'gene_sets/LGDs_male_iossifov_2014_affected.csv',
//           'gene_sets/LGDs_iossifov_2014_unaffected.csv'
//         ]
//       }
//     },
//     {
//       peopleGroup: 'unaffected',
//       expectedConditions: {
//         effectTypesSearchQueries: ['LGDs'],
//         expectedGeneSymbolsFiles: ['gene_sets/LGDs_iossifov_2014_unaffected.csv']
//       }
//     }
//   ], (data) => {
//     it('should download iossifov ' + data.peopleGroup + ' denovo gene sets ' +
//        'and check whether they are equal to the reference data', () => {
//       const expectedGeneSymbolsSet = new Set();
//       const downloadedGeneSymbolsSet = new Set();
//       const downloadedGeneSymbolsFilePath = browser.params.genesetsDownloadPath + browser.params.genesetsFileName;

//       if (!fs.existsSync(browser.params.genesetsDownloadPath)) {
//         fs.mkdirSync(browser.params.genesetsDownloadPath);
//       }

//       if (fs.existsSync(downloadedGeneSymbolsFilePath)) {
//         fs.unlinkSync(downloadedGeneSymbolsFilePath);
//       }

//       genotypeBrowserController.setStudy(datasetIds.iossifov2014);

//       genesBlockPage.geneSetsButton.click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.geneSetsPanel);
//       genesBlockPage.geneSetsCollectionSelectorDropdownMenu.click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.findGeneSetsCollectionOptionByText('Denovo'));
//       genesBlockPage.findGeneSetsCollectionOptionByText('Denovo').click();
//       genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.geneSetsPanel);

//       // By default, the checkbox 'affected' for the current dataset is checked.
//       // In the case of data.peopleGroup === 'affected', do nothing.
//       // If the data.peopleGroup is 'unaffected' though, uncheck affected and check unaffected checkbox.

//       if (data.peopleGroup === 'unaffected') {
//         genesBlockPage.findDenovoGeneSetCollectionCheckbox('iossifov_2014', 'affected').click();
//         genesBlockPage.findDenovoGeneSetCollectionCheckbox('iossifov_2014', 'unaffected').click();
//       }
//       genesBlockPage.geneSetsSearchbox.click();

//       for (let i = 0; i < data.expectedConditions.effectTypesSearchQueries.length; i++) {
//         expectedGeneSymbolsSet.clear();
//         downloadedGeneSymbolsSet.clear();

//         genesBlockPage.geneSetsSearchbox.type(data.expectedConditions.effectTypesSearchQueries[i]);
//         genesBlockPage.browserWaitForVisibilityOfElement(genesBlockPage.getFirstGeneSetFromDropdownMenu());

//         (genesBlockPage.getFirstGeneSetFromDropdownMenu()).click();
//         genesBlockPage.downloadButton.click();
//         browser.driver.wait(() => {
//           return fs.existsSync(downloadedGeneSymbolsFilePath);
//         }, 30000);
//         new Promise<void>((resolve) => {
//           fs.createReadStream(downloadedGeneSymbolsFilePath)
//           .pipe(csv())
//           .on('data', (d) => downloadedGeneSymbolsSet.add(Object.values(d)))
//           .on('end', () => {
//             fs.unlinkSync(downloadedGeneSymbolsFilePath);
//             resolve();
//           });
//         });
//         new Promise<void>((resolve) => {
//           fs.createReadStream(browser.params.fixturesFolderPath + data.expectedConditions.expectedGeneSymbolsFiles[i])
//           .pipe(csv())
//           .on('data', (d) => expectedGeneSymbolsSet.add(Object.values(d)))
//           .on('end', () => {
//             resolve();
//           });
//         });
//         expect(areSetsEqual(downloadedGeneSymbolsSet, expectedGeneSymbolsSet)).toBe(true);
//         genesBlockPage.selectedGeneSet.click();
//       }
//     });
//   });
// });
