import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { GenomicScoresBlockPage } from 'cypress/elements/genomic-scores-block-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';
import { GenotypePreviewTablePage } from 'cypress/elements/genotype-preview-table-page';
import { PersonFiltersBlockPage } from 'cypress/elements/person-filters-block-page';
import { RegionsBlockPage } from 'cypress/elements/regions-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Genotype browser tests', () => {
  const page = new GenotypeBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display regions block panel in the genotype browser', () => {
    const regionsBlockPage = new RegionsBlockPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    regionsBlockPage.block.should('be.visible');
  });

  it('should display genes block panel in the genotype browser', () => {
    const genesBlockPage = new GenesBlockPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    genesBlockPage.window.should('be.visible');
  });

  it('should display genotype block panel in the genotype browser', () => {
    const genotypeBlockPage = new GenotypeBlockPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.window.should('be.visible');
  });

  it('should display genomic scores panel in the genotype browser', () => {
    const genomicScoresBlockPage = new GenomicScoresBlockPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    genomicScoresBlockPage.block.should('be.visible');
  });

  it('should display family filters block panel in the genotype browser', () => {
    const familyFilterBlockPage = new FamilyFilterBlockPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    familyFilterBlockPage.window.should('be.visible');
  });

  it('should display person filters block in the genotype browser', () => {
    const personFiltersBlockPage = new PersonFiltersBlockPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    personFiltersBlockPage.block.should('be.visible');
  });

  it('should display "Table Preview" button in the genotype browser', () => {
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    page.tablePreviewButton.should('be.visible');
  });

  it('should display "Share query" button in the genotype browser', () => {
    const saveQueryPage = new SaveQueryPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    saveQueryPage.button.should('be.visible');
  });

  it('should display "Save query" button in the genotype browser', () => {
    const saveQueryPage = new SaveQueryPage();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    saveQueryPage.button.should('be.visible');
  });

  it('should display "Download" button in the genotype browser', () => {
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    page.downloadButton.should('be.visible');
  });

  it('should display genotype preview table after table preview button click', () => {
    const genotypePreviewTablePage = new GenotypePreviewTablePage();
    const genotypeBrowserController = new GenotypeBrowserController();

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    genotypePreviewTablePage.table.should('not.exist');

    genotypeBrowserController.pressTablePreviewButton();
    genotypePreviewTablePage.table.should('be.visible');
  });

  it('should hide table preview results after changing a filter', () => {
    const genotypePreviewTablePage = new GenotypePreviewTablePage();
    const genotypeBlockPage = new GenotypeBlockPage();
    const genotypeBrowserController = new GenotypeBrowserController();

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);
    genotypeBrowserController.pressTablePreviewButton();
    genotypePreviewTablePage.table.should('be.visible');

    genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', 'affected').click();
    genotypePreviewTablePage.table.should('not.exist');
  });
});

describe('Genotype browser table preview result tests', () => {
  const page = new GenotypeBrowserPage();
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
    {study: datasetIds.compAll, count: '30'},
    {study: datasetIds.compDenovo, count: '5'},
    {study: datasetIds.compVcf, count: '25'},
    {study: datasetIds.iossifov2014, count: '0'},
    {study: datasetIds.multi, count: '0'}
  ].forEach(data => {
    it('should display the correct overview paragraph ' +
       'when gene symbol is "SAMD11" at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.filterGenesByGeneSymbol('SAMD11');
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.count + ' variants selected');
    });
  });

  [
    {region: '1:865582', count: '5'},
    {region: '1:865583', count: '5'},
    {region: '1:865624', count: '5'},
    {region: '1:865627', count: '5'},
    {region: '1:865664', count: '3'},
    {region: '1:865691', count: '2'}
  ].forEach(data => {
    it('should display the correct overview paragraph' +
       'when regions filter is "' + data.region + '" at /comp_vcf/browser', () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setRegion(data.region);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.count + ' variants selected');
    });
  });

  [
    {
      study: datasetIds.compAll,
      affectedStatus: 'affected',
      overviewParagraph: '30 variants selected'
    },
    {
      study: datasetIds.compDenovo,
      affectedStatus: 'affected',
      overviewParagraph: '5 variants selected'
    },
    {
      study: datasetIds.compVcf,
      affectedStatus: 'affected',
      overviewParagraph: '25 variants selected'
    },
    {
      study: datasetIds.multi,
      affectedStatus: 'affected',
      overviewParagraph: '1 variant selected'
    },
    {
      study: datasetIds.compAll,
      affectedStatus: 'unaffected',
      overviewParagraph: '25 variants selected'
    },
    {
      study: datasetIds.compDenovo,
      affectedStatus: 'unaffected',
      overviewParagraph: '0 variants selected'
    },
    {
      study: datasetIds.compVcf,
      affectedStatus: 'unaffected',
      overviewParagraph: '25 variants selected'
    },
    {
      study: datasetIds.multi,
      affectedStatus: 'unaffected',
      overviewParagraph: '2 variants selected'
    }
  ].forEach(data => {
    it('should display the correct overview paragraph when ' +
      'affected status - ' + data.affectedStatus + ' is checked at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setAffectedStatus(data.affectedStatus);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.overviewParagraph);
    });
  });

  [
    {childGender: 'male', count: '23'},
    {childGender: 'female', count: '22'},
    {childGender: 'unspecified', count: '0'}
  ].forEach(data => {
    it('should display the correct data in overview paragraph when child gender is ' + data.childGender, () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setGender(data.childGender);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.count + ' variants selected');
    });
  });

  [
    {variantType: 'sub', count: '25'},
    {variantType: 'ins', count: '0'},
    {variantType: 'del', count: '0'}
  ].forEach(data => {
    it('should display the correct data in overview paragraph when only ' +
      data.variantType + ' variant type checkbox is checked', () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setVariantType(data.variantType);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.count + ' variants selected');
    });
  });

  [
    {effectType: 'All', count: '25'},
    {effectType: 'LGDs', count: '0'},
    {effectType: 'Nonsynonymous', count: '12'},
    {effectType: 'Coding', count: '25'},
    {effectType: 'UTRs', count: '0'}
  ].forEach(data => {
    it('should display the correct data in overview paragraph where effect types are ' + data.effectType, () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setEffectTypesGroup(data.effectType);
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.count + ' variants selected');
    });
  });

  [
    {
      study: datasetIds.compAll,
      inheritanceType: 'mendelian',
      overviewParagraph: '25 variants selected'
    },
    {
      study: datasetIds.compDenovo,
      inheritanceType: 'mendelian',
      overviewParagraph: '0 variants selected'
    },
    {
      study: datasetIds.compVcf,
      inheritanceType: 'mendelian',
      overviewParagraph: '25 variants selected'
    },
    {
      study: datasetIds.iossifov2014,
      inheritanceType: 'mendelian',
      overviewParagraph: '0 variants selected'
    },
    {
      study: datasetIds.multi,
      inheritanceType: 'mendelian',
      overviewParagraph: '2 variants selected'
    },
    {
      study: datasetIds.compAll,
      inheritanceType: 'denovo',
      overviewParagraph: '5 variants selected'
    },
    {
      study: datasetIds.compDenovo,
      inheritanceType: 'denovo',
      overviewParagraph: '5 variants selected'
    },
    {
      study: datasetIds.compVcf,
      inheritanceType: 'denovo',
      overviewParagraph: '0 variants selected'
    },
    {
      study: datasetIds.multi,
      inheritanceType: 'denovo',
      overviewParagraph: '0 variants selected'
    }
  ].forEach(data => {
    it('should display the correct overview paragraph when ' +
       'inheritance types are ' + data.inheritanceType + ' at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.setInheritanceType(data.inheritanceType);
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.overviewParagraph);
    });
  });

  [
    {study: datasetIds.compAll, overviewParagraph: '5 variants selected'},
    {study: datasetIds.compDenovo, overviewParagraph: '5 variants selected'},
    {study: datasetIds.compVcf, overviewParagraph: '0 variants selected'},
    {study: datasetIds.multi, overviewParagraph: '0 variants selected'}
  ].forEach(data => {
    it('should display the correct overview paragraph when ' +
       'inheritance types are denovo at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.setInheritanceType('denovo');
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.overviewParagraph);
    });
  });

  [
    {familyId: 'f1', count: '4'},
    {familyId: 'f2', count: '5'},
    {familyId: 'f3', count: '4'},
    {familyId: 'f4', count: '6'},
    {familyId: 'f5', count: '6'}
  ].forEach(data => {
    it('should display the correct overview paragraph when family id is "' + data.familyId + '"', () => {
      genotypeBrowserController.setStudy(datasetIds.compVcf);
      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.setFamilyFilterToId(data.familyId);
      genotypeBrowserController.pressTablePreviewButton();

      page.overviewParagraph.should('have.text', data.count + ' variants selected');
    });
  });

  [
    {
      study: datasetIds.iossifov2014,
      geneSymbol: 'SCN2A',
      effectType: 'LGDs',
      overviewParagraph: '2 variants selected'
    },
    {
      study: datasetIds.iossifov2014,
      geneSymbol: 'NRXN1',
      effectType: 'LGDs',
      overviewParagraph: '1 variant selected'
    },
    {
      study: datasetIds.iossifov2014,
      geneSymbol: 'NRXN1',
      effectType: 'All',
      overviewParagraph: '1 variant selected'
    }
  ].forEach(data => {
    it('should display the correct overview paragraph when effect types are ' +
      data.effectType + ' and gene symbol is "' + data.geneSymbol + '" at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(data.study);
      genotypeBrowserController.setEffectTypesGroup(data.effectType);
      genotypeBrowserController.filterGenesByGeneSymbol(data.geneSymbol);
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.overviewParagraph);
    });
  });

  it('should display "2 variants selected" in overview paragraph ' +
     'when family id is 11002 at /iossifov_2014/browser', () => {
    genotypeBrowserController.setStudy(datasetIds.iossifov2014);
    genotypeBrowserController.setEffectTypesGroup('All');
    genotypeBrowserController.setFamilyFilterToId('11002');
    genotypeBrowserController.pressTablePreviewButton();
    page.overviewParagraph.should('have.text', '2 variants selected');
  });

  it('should display "0 variants selected" in overview paragraph when the gene sets is ' +
     'GO Terms - GO:0016917 GABA_receptor_activity and effect types are LGDs at /iossifov_2014/browser', () => {
    genotypeBrowserController.setStudy(datasetIds.iossifov2014);
    genotypeBrowserController.filterGenesByGeneSets('GO Terms', 'GO:0016917');
    genotypeBrowserController.setEffectTypesGroup('LGDs');
    genotypeBrowserController.pressTablePreviewButton();
    page.overviewParagraph.should('have.text', '0 variants selected');
  });

  [
    {
      study: datasetIds.iossifov2014,
      collection: 'GO Terms',
      geneSet: 'GO:0016917',
      effectTypes: ['missense'],
      count: '4'
    },
    {
      study: datasetIds.iossifov2014,
      collection: 'GO Terms',
      geneSet: 'GO:0016917',
      effectTypes: ['missense', 'synonymous'],
      count: '5'
    }
  ].forEach(data => {
    it('should display the correct overview paragraph when gene sets is ' +
       data.collection + '- ' + data.geneSet + ' and effect types are ' + data.effectTypes.toString() +
       ' at /' + data.study + '/browser', () => {
      genotypeBrowserController.setStudy(datasetIds.iossifov2014);
      genotypeBrowserController.filterGenesByGeneSets('GO Terms', 'GO:0016917');
      genotypeBrowserController.setEffectTypes(data.effectTypes);
      genotypeBrowserController.pressTablePreviewButton();
      page.overviewParagraph.should('have.text', data.count + ' variants selected');
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
      genotypeBrowserController.pressTablePreviewButton();

      genotypePreviewTablePage.getSpansInTableRowByIndex(7).eq(0).invoke('text').then(text => {
        expect(truncate(text)).to.be.eq(data.values.age);
      });

      genotypePreviewTablePage.getSpansInTableRowByIndex(7).eq(1).invoke('text').then(text => {
        expect(truncate(text)).to.be.eq(data.values.iq);
      });
    });
  });

  it('should display the correct overview paragraph with denovo inheritance types, affected only, 5\'UTR', () => {
    const genotypeBlockPage = new GenotypeBlockPage();

    genotypeBrowserController.setStudy(datasetIds.iossifov2014);
    genotypeBrowserController.setInheritanceType('denovo');
    genotypeBrowserController.setAffectedStatus('affected');
    genotypeBrowserController.setEffectTypesGroup('None');
    genotypeBlockPage.findCheckboxInComponentContainingText('gpf-effect-types', '5\'UTR').click();

    genotypeBrowserController.pressTablePreviewButton();
    page.overviewParagraph.should('have.text', '98 variants selected');
  });
});

describe('Genotype browser family variants download tests', () => {
  const genotypeBrowserController = new GenotypeBrowserController();
  const page = new GenotypeBrowserPage();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome(false);
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  it.skip('should download all effect types CHD8 iossifov variants ' +
     'and validate whether they are equal to the reference data', () => {
    const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/variants.tsv';
    const expectedVariantsPath = 'cypress/fixtures/genotype-browser/variants.tsv';

    genotypeBrowserController.setStudy(datasetIds.iossifov2014);
    genotypeBrowserController.setEffectTypesGroup('All');
    genotypeBrowserController.filterGenesByGeneSymbol('CHD8');

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

describe('Genotype browser UCSC url tests', () => {
  const genotypeBrowserController = new GenotypeBrowserController();
  const genotypePreviewTablePage = new GenotypePreviewTablePage();

  before(() => {
    genotypeBrowserController.cleanup();
    genotypeBrowserController.navigateToHome(false);
    genotypeBrowserController.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserController.preserveLogin();
    genotypeBrowserController.navigateToHome();
  });

  it('should compare redirect links', () => {
    genotypeBrowserController.setStudy(datasetIds.compAll);
    genotypeBrowserController.setEffectTypesGroup('All');
    genotypeBrowserController.pressTablePreviewButton();

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

