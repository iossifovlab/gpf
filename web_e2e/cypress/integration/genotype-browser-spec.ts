import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { GenomicScoresBlockPage } from 'cypress/elements/genomic-scores-block-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';
import { GenotypePreviewTablePage } from 'cypress/elements/genotype-preview-table-page';
import { RegionsBlockPage } from 'cypress/elements/regions-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Genotype browser tests', () => {
  const page = new GenotypeBrowserPage();
  const datasetList = [
    datasetIds.compAll, datasetIds.compDenovo, datasetIds.compVcf, datasetIds.iossifov2014, datasetIds.multi
  ];

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.loginAdmin();
  });

  afterEach(() => {
    page.logout();
  });

  datasetList.forEach(dataset => {
    it('should display regions block panel in genotype browser at /' + dataset + '/browser', () => {
      const regionsBlockPage = new RegionsBlockPage();
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      regionsBlockPage.block.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it.only('should display genes block panel in genotype browser at /' + dataset + '/browser', () => {
      const genesBlockPage = new GenesBlockPage();
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      genesBlockPage.window.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it('should display genotype block panel in genotype browser at /' + dataset + '/browser', () => {
      const genotypeBlockPage = new GenotypeBlockPage();
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      genotypeBlockPage.window.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it.only('should display genomic scores panel in genotype browser at /' + dataset + '/browser', () => {
      const genomicScoresBlockPage = new GenomicScoresBlockPage();
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      genomicScoresBlockPage.block.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it.only('should display family filters block panel in genotype browser at /' + dataset + '/browser', () => {
      const familyFilterBlockPage = new FamilyFilterBlockPage();
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      familyFilterBlockPage.window.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it.only('should display "Table Preview" button in genotype browser at /' + dataset + '/browser', () => {
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      page.tablePreviewButton.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it('should display "Share query" button in genotype browser at /' + dataset + '/browser', () => {
      const shareQueryPage = new ShareQueryPage();
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      shareQueryPage.button.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it('should display "Save query" button in genotype browser at /' + dataset + '/browser', () => {
      const saveQueryPage = new SaveQueryPage();
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      saveQueryPage.button.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it.only('should display "Download" button in genotype browser at /' + dataset + '/browser', () => {
      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      page.downloadButton.should('be.visible');
    });
  });

  datasetList.forEach(dataset => {
    it.only('should display genotype preview table after table preview button click at /' + dataset + '/browser', () => {
      const genotypePreviewTablePage = new GenotypePreviewTablePage();

      page.navigateToDatasetPage(dataset, toolPageLinks.genotypeBrowser);
      genotypePreviewTablePage.table.should('not.exist');

      page.tablePreviewButton.click();
      genotypePreviewTablePage.table.should('be.visible');
    });
  });
});

describe('Genotype browser table preview result tests', () => {
  const page = new GenotypeBrowserPage();
  const genotypeBrowserController = new GenotypeBrowserController();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome();
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  [
    {study: datasetIds.compAll, expectedOverviewParagraph: '35 variants selected (35 shown)'},
    {study: datasetIds.compDenovo, expectedOverviewParagraph: '5 variants selected (5 shown)'},
    {study: datasetIds.compVcf, expectedOverviewParagraph: '30 variants selected (30 shown)'},
    {study: datasetIds.iossifov2014, expectedOverviewParagraph: '0 variants selected (0 shown)'},
    {study: datasetIds.multi, expectedOverviewParagraph: '0 variants selected (0 shown)'}
  ].forEach(data => {
    it('should display the correct data in overview paragraph ' +
       'when gene symbol is "SAMD11" at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.filterGenesByGeneSymbol('SAMD11');
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  [
    {region: '1:865582'}, {region: '1:865583'},
    {region: '1:865624'}, {region: '1:865627'},
    {region: '1:865664'}, {region: '1:865691'}
  ].forEach(data => {
    it('should display "5 variants selected" in overview paragraph when regions filter is "' +
       data.region + '" at /comp_vcf/browser', () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setRegion(data.region);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', '5 variants selected (5 shown)');
    });
  });

  [
    {
      study: datasetIds.compAll,
      affectedStatus: 'affected',
      expectedOverviewParagraph: '35 variants selected (35 shown)'
    },
    {
      study: datasetIds.compDenovo,
      affectedStatus: 'affected',
      expectedOverviewParagraph: '5 variants selected (5 shown)'
    },
    {
      study: datasetIds.compVcf,
      affectedStatus: 'affected',
      expectedOverviewParagraph: '30 variants selected (30 shown)'
    },
    {
      study: datasetIds.iossifov2014,
      affectedStatus: 'affected',
      expectedOverviewParagraph: 'more than 1000 variants selected (1000 shown)'
    },
    {
      study: datasetIds.multi,
      affectedStatus: 'affected',
      expectedOverviewParagraph: '1 variant selected (1 shown)'
    },
    {
      study: datasetIds.compAll,
      affectedStatus: 'unaffected',
      expectedOverviewParagraph: '30 variants selected (30 shown)'
    },
    {
      study: datasetIds.compDenovo,
      affectedStatus: 'unaffected',
      expectedOverviewParagraph: '0 variants selected (0 shown)'
    },
    {
      study: datasetIds.compVcf,
      affectedStatus: 'unaffected',
      expectedOverviewParagraph: '30 variants selected (30 shown)'
    },
    {
      study: datasetIds.iossifov2014,
      affectedStatus: 'unaffected',
      expectedOverviewParagraph: 'more than 1000 variants selected (1000 shown)'
    },
    {
      study: datasetIds.multi,
      affectedStatus: 'unaffected',
      expectedOverviewParagraph: '2 variants selected (2 shown)'
    }
  ].forEach(data => {
    it('should display "' + data.expectedOverviewParagraph + '" in overview paragraph when ' +
      'affected status - ' + data.affectedStatus + ' is checked at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setAffectedStatus(data.affectedStatus);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  [
    {childGender: 'male', expectedOverviewParagraph: '28 variants selected (28 shown)'},
    {childGender: 'female', expectedOverviewParagraph: '27 variants selected (27 shown)'},
    {childGender: 'unspecified', expectedOverviewParagraph: '0 variants selected (0 shown)'}
  ].forEach(data => {
    it('should display the correct data in overview paragraph when child gender is ' + data.childGender, () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setGender(data.childGender);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  [
    {variantType: 'sub', expectedOverviewParagraph: '30 variants selected (30 shown)'},
    {variantType: 'ins', expectedOverviewParagraph: '0 variants selected (0 shown)'},
    {variantType: 'del', expectedOverviewParagraph: '0 variants selected (0 shown)'}
  ].forEach(data => {
    it('should display the correct data in overview paragraph when only ' +
      data.variantType + ' variant type checkbox is checked', () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setVariantType(data.variantType);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  [
    {effectType: 'All', expectedOverviewParagraph: '30 variants selected (30 shown)'},
    {effectType: 'LGDs', expectedOverviewParagraph: '0 variants selected (0 shown)'},
    {effectType: 'Nonsynonymous', expectedOverviewParagraph: '15 variants selected (15 shown)'},
    {effectType: 'Coding', expectedOverviewParagraph: '30 variants selected (30 shown)'},
    {effectType: 'UTRs', expectedOverviewParagraph: '0 variants selected (0 shown)'}
  ].forEach(data => {
    it('should display the correct data in overview paragraph whene effect types are ' + data.effectType, () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setEffectTypesGroup(data.effectType);
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  [
    {
      study: datasetIds.compAll,
      inheritanceType: 'mendelian',
      expectedOverviewParagraph: '30 variants selected (30 shown)'
    },
    {
      study: datasetIds.compDenovo,
      inheritanceType: 'mendelian',
      expectedOverviewParagraph: '0 variants selected (0 shown)'
    },
    {
      study: datasetIds.compVcf,
      inheritanceType: 'mendelian',
      expectedOverviewParagraph: '30 variants selected (30 shown)'
    },
    {
      study: datasetIds.iossifov2014,
      inheritanceType: 'mendelian',
      expectedOverviewParagraph: '0 variants selected (0 shown)'
    },
    {
      study: datasetIds.multi,
      inheritanceType: 'mendelian',
      expectedOverviewParagraph: '2 variants selected (2 shown)'
    },
    {
      study: datasetIds.compAll,
      inheritanceType: 'denovo',
      expectedOverviewParagraph: '5 variants selected (5 shown)'
    },
    {
      study: datasetIds.compDenovo,
      inheritanceType: 'denovo',
      expectedOverviewParagraph: '5 variants selected (5 shown)'
    },
    {
      study: datasetIds.compVcf,
      inheritanceType: 'denovo',
      expectedOverviewParagraph: '0 variants selected (0 shown)'
    },
    {
      study: datasetIds.iossifov2014,
      inheritanceType: 'denovo',
      expectedOverviewParagraph: 'more than 1000 variants selected (1000 shown)'
    },
    {
      study: datasetIds.multi,
      inheritanceType: 'denovo',
      expectedOverviewParagraph: '0 variants selected (0 shown)'
    }
  ].forEach(data => {
    it('should display "' + data.expectedOverviewParagraph + '" in overview paragraph when ' +
       'inheritance types are ' + data.inheritanceType + ' at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.setInheritanceType(data.inheritanceType);
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  [
    {study: datasetIds.compAll, expectedOverviewParagraph: '5 variants selected (5 shown)'},
    {study: datasetIds.compDenovo, expectedOverviewParagraph: '5 variants selected (5 shown)'},
    {study: datasetIds.compVcf, expectedOverviewParagraph: '0 variants selected (0 shown)'},
    {study: datasetIds.iossifov2014, expectedOverviewParagraph: 'more than 1000 variants selected (1000 shown)'},
    {study: datasetIds.multi, expectedOverviewParagraph: '0 variants selected (0 shown)'}
  ].forEach(data => {
    it('should display "' + data.expectedOverviewParagraph + '" in overview paragraph when ' +
       'inheritance types are denovo at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.setInheritanceType('denovo');
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  [
    {familyId: 'f1'},
    {familyId: 'f2'},
    {familyId: 'f3'},
    {familyId: 'f4'},
    {familyId: 'f5'}
  ].forEach(data => {
    it('should display "6 variants selected" in overview paragraph when family id is "' + data.familyId + '"', () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.setFamilyFilterToId(data.familyId);
      genotypeBrowserController.showTablePreview();

      page.overviewParagraph.should('have.text', '6 variants selected (6 shown)');
    });
  });

  [
    {
      study: datasetIds.iossifov2014,
      geneSymbol: 'SCN2A',
      effectType: 'LGDs',
      expectedOverviewParagraph: '2 variants selected (2 shown)'
    },
    {
      study: datasetIds.iossifov2014,
      geneSymbol: 'NRXN1',
      effectType: 'LGDs',
      expectedOverviewParagraph: '1 variant selected (1 shown)'
    },
    {
      study: datasetIds.iossifov2014,
      geneSymbol: 'NRXN1',
      effectType: 'All',
      expectedOverviewParagraph: '1 variant selected (1 shown)'
    }
  ].forEach(data => {
    it('should display "' + data.expectedOverviewParagraph + '" in overview paragraph when effect types are ' +
      data.effectType + ' and gene symbol is "' + data.geneSymbol + '" at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setEffectTypesGroup(data.effectType);
      genotypeBrowserController.filterGenesByGeneSymbol(data.geneSymbol);
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  it('should display "2 variants selected" in overview paragraph ' +
     'when family id is 11002 at /iossifov_2014/browser', () => {
    genotypeBrowserController.setStudy(datasetIds.iossifov2014);
    genotypeBrowserController.setEffectTypesGroup('All');
    genotypeBrowserController.setFamilyFilterToId('11002');
    genotypeBrowserController.showTablePreview();
    page.overviewParagraph.should('have.text', '2 variants selected (2 shown)');
  });

  it('should display "0 variants selected" in overview paragraph when the gene sets is ' +
     'GO Terms - GO:0016917 GABA_receptor_activity and effect types are LGDs at /iossifov_2014/browser', () => {
    genotypeBrowserController.setStudy(datasetIds.iossifov2014);
    genotypeBrowserController.filterGenesByGeneSets('GO Terms', 'GO:0016917');
    genotypeBrowserController.setEffectTypesGroup('LGDs');
    genotypeBrowserController.showTablePreview();
    page.overviewParagraph.should('have.text', '0 variants selected (0 shown)');
  });

  [
    {
      study: datasetIds.iossifov2014,
      collection: 'GO Terms',
      geneSet: 'GO:0016917',
      effectTypes: ['Missense'],
      expectedOverviewParagraph: '4 variants selected (4 shown)'
    },
    {
      study: datasetIds.iossifov2014,
      collection: 'GO Terms',
      geneSet: 'GO:0016917',
      effectTypes: ['Missense', 'Synonymous'],
      expectedOverviewParagraph: '5 variants selected (5 shown)'
    }
  ].forEach(data => {
    it('should display "' + data.expectedOverviewParagraph + '" in overview paragraph when gene sets is ' +
       data.collection + '- ' + data.geneSet + ' and effect types are ' + data.effectTypes.toString() +
       ' at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(datasetIds.iossifov2014);
      genotypeBrowserController.filterGenesByGeneSets('GO Terms', 'GO:0016917');
      genotypeBrowserController.setEffectTypes(data.effectTypes);
      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data.expectedOverviewParagraph);
    });
  });

  function truncate(num, places = 3): number {
    return Math.trunc(num * Math.pow(10, places)) / Math.pow(10, places);
  }

  [
    {familyId: 'f1', values: {age: 166.339, iq: 104.911}},
    {familyId: 'f2', values: {age: 111.538, iq: 66.694}},
    {familyId: 'f3', values: {age: 68.001, iq: 69.333}},
    {familyId: 'f4', values: {age: 157.618, iq: 103.074}},
    {familyId: 'f5', values: {age: 171.890, iq: 38.885}}
  ].forEach(data => {
    it('should display the correct age and iq values in the measures column for "' + data.familyId + '" family', () => {
      const genotypePreviewTablePage = new GenotypePreviewTablePage();

      genotypeBrowserController.setStudy(datasetIds.compAll);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.setFamilyFilterToId(data.familyId);
      genotypeBrowserController.showTablePreview();

      genotypePreviewTablePage.getSpansInTableRowByIndex(7).eq(0).invoke('text').then(text => {
        expect(truncate(text)).to.be.eq(data.values.age);
      });

      genotypePreviewTablePage.getSpansInTableRowByIndex(7).eq(1).invoke('text').then(text => {
        expect(truncate(text)).to.be.eq(data.values.iq);
      });
    });
  });
});

describe('Genotype browser family variants download tests', () => {
  const genotypeBrowserController = new GenotypeBrowserController();
  const page = new GenotypeBrowserPage();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome();
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  it.only('should download all effect types CHD8 iossifov variants ' +
     'and validate whether they are equal to the reference data', () => {
    const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/variants.tsv';
    const expectedVariantsPath = 'cypress/fixtures/genotype-browser/variants.tsv';

    genotypeBrowserController.setStudy(datasetIds.iossifov2014);
    genotypeBrowserController.setEffectTypesGroup('All');
    genotypeBrowserController.filterGenesByGeneSymbol('CHD8');

    cy.window().document().then(function (doc) {
      doc.addEventListener('click', () => {
        setTimeout(function () { doc.location.reload() }, 5000)
      })
      page.downloadButton.click();
    });

    cy.readFile(downloadedVariantsPath, { timeout: 5000 }).then(downloadedFile => {
      cy.readFile(expectedVariantsPath, { timeout: 5000 }).then(expectedFile => {
        const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
        const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
        expect(downloadedFileLines).to.deep.eq(expectedFileLines);
      });
    });
  });
});

describe('Genotype browser UCSC url tests', () => {
  const genotypeBrowserController = new GenotypeBrowserController();
  const genotypePreviewTablePage = new GenotypePreviewTablePage();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome();
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  it('should compare redirect links', () => {
    genotypeBrowserController.setStudy(datasetIds.compAll);
    genotypeBrowserController.setEffectTypesGroup('All');
    genotypeBrowserController.showTablePreview();

    const baseUrl = 'http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr';
    for (let index = 0; index <= 10; index++) {
      genotypePreviewTablePage.getSpansInTableRow(index, 1).eq(0).then(element => {
        cy.wrap(element).within(span => {
          cy.wrap(span).get('a').should('have.attr', 'href').then(url => {
            expect(url).to.equal(baseUrl + span.text());
          });
        });
      });
    }
  });
});

describe('Genotype browser table preview visual tests', () => {
  const genotypeBrowserController = new GenotypeBrowserController();
  const page = new GenotypeBrowserPage();
  const genotypePreviewTablePage = new GenotypePreviewTablePage();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome();
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  it('should compare POGZ and KDM5B gene results', () => {
    const genesBlockPage = new GenesBlockPage();

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneSymbolsButton.click();

    [['POGZ', '2', 'pogz'], ['KDM5B', '4','kdm5b']].forEach(data => {
      genesBlockPage.geneSymbolsTextarea.clear().type(data[0]);

      genotypeBrowserController.showTablePreview();
      page.overviewParagraph.should('have.text', data[1] +' variants selected (' + data[1] + ' shown)');
      genotypePreviewTablePage.table.matchImageSnapshot(data[2]);
    });
  });
});
