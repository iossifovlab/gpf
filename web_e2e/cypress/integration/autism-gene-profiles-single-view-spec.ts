import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles single view tests', () => {
  const page = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should display header', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.header.should('be.visible');
    page.header.should('have.text', 'CHD8');
  });

  it('should display the autism scores table', () => {
    page.autismScoresTable.should('be.visible');
    page.autismScoresTable.find('th').should('have.text', 'Autism Scores');
    page.autismScoresTable.find('tr').should('have.length', 1);
  });

  it('should display the protection scores table', () => {
    page.protectionScoresTable.should('be.visible');
    page.protectionScoresTable.find('th').should('have.text', 'Protection Scores');
    page.protectionScoresTable.find('tr').should('have.length', 4);
  });

  it('should display the single scores markers', () => {
    page.singleScoreMarkers.should('have.length', 5);
  });

  it('should display the autism gene sets table', () => {
    page.geneAutismGeneSetsTable.should('be.visible');
    page.geneAutismGeneSetsTable.find('th').should('have.text', 'Autism Gene Sets');
    page.geneAutismGeneSetsTable.find('tr').should('have.length', 2);
  });

  it('should display the relevant gene sets table', () => {
    page.geneRelevantGeneSetsTable.should('be.visible');
    page.geneRelevantGeneSetsTable.find('th').should('have.text', 'Relevant Gene Sets');
    page.geneRelevantGeneSetsTable.find('tr').should('have.length', 4);
  });

  it('should display the datasets table', () => {
    page.datasetsTable.should('be.visible');
    page.datasetsTable.find('th').first().should('have.text', 'iossifov_2014');
    page.datasetsTable.find('tr').should('have.length', 5);
  });
});

describe('Autism gene profiles single view links tests', () => {
  const page = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should display gene browser link', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.geneBrowserLink.should('be.visible');
    page.geneBrowserLink.should('have.text', 'Gene Browser');
  });

  it('should display UCSC link', () => {
    page.UCSCLink.should('be.visible');
    page.UCSCLink.should('have.text', 'UCSC genome browser');
  });

  it('should display GeneCards link', () => {
    page.geneCardsLink.should('be.visible');
    page.geneCardsLink.should('have.text', 'GeneCards');
  });

  it('should display Pubmed link', () => {
    page.pubmedLink.should('be.visible');
    page.pubmedLink.should('have.text', 'Pubmed');
  });

  it('should have the correct href for the gene browser link', () => {
    page.header.invoke('text').then((headerText) => {
      const baseUrl = Cypress.config().baseUrl;
      const headerName = headerText;
      const geneBrowserUrl = `${baseUrl}datasets/ALL_genotypes/gene-browser/${headerName}`;
      page.geneBrowserLink.should('have.prop', 'href').and('equal', geneBrowserUrl)
    });
  });

  it('should have the correct href for the UCSC link', () => {
    const UCSCLink = 'https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr14%3A21853353-21905457';
    page.UCSCLink.should('have.prop', 'href').and('equal', UCSCLink)
  });

  it('should have the correct href for the GeneCards link', () => {
    const geneCardsLink = 'https://www.genecards.org/cgi-bin/carddisp.pl?gene=CHD8';
    page.geneCardsLink.should('have.prop', 'href').and('equal', geneCardsLink)
  });

  it('should have the correct href for the Pubmed link', () => {
    const pubmedLink = 'https://pubmed.ncbi.nlm.nih.gov/?term=CHD8%20AND%20(autism%20OR%20asd)';
    page.pubmedLink.should('have.prop', 'href').and('equal', pubmedLink)
  });
});

describe('Single view study table', () => {
  const page = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  it.skip('should test redirect logic', () => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);

    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type('GRIN2B');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=GRIN2B&sortBy=autism_gene_sets_rank&order=desc').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView('GRIN2B');

    cy.intercept({
      method: 'POST',
      url: '/gpf/api/v3/query_state/save'
    }).as('query');
    cy.get('#denovo_missense > :nth-child(2) > .link-genotype-browser > span').then(value => {      
      cy.wrap(value).parent().parent().parent().invoke('attr', 'id').then(effectType => {
        cy.wrap(effectType).as('effectType');
      });
      cy.wrap(value).click();
    });
    cy.get('@query').then(req => {
      if(req !== null) {
        const genotypeBlockPage = new GenotypeBlockPage();
        cy.visit(Cypress.config().baseUrl + '/load-query/' + req.response.body.uuid);
        genotypeBlockPage.findCheckboxInComponentContainingText('.pedigree-selector-card', 'affected').parent().within(checkBoxes => {
          cy.wrap(checkBoxes).get('input').should('be.checked');
          cy.get('@effectType').then(effectType => {
            page.getStudyExpectedDataFromGenotype(effectType);
          });
        });
        page.getStudyActualDataFromGenotype();
        cy.get('@genotypeExpectedWrapper').then(expected => {
          cy.get('@genotypeActualWrapper').then(actual => {
            expect(expected).to.deep.equal(actual);
          });
        });
      }
    });
  });
});

describe('Autism gene profiles single view visual tests', () => {
  const page = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should compare histrograms', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();

    [{tableId: 'autism_scores', tableRows: ['SFARI_gene_score']},
     {tableId: 'protection_scores', tableRows: ['RVIS_rank', 'LGD_rank', 'pLI_rank', 'pRec_rank']}
    ].forEach((data, dataIndex) => {
      cy.get('#' + data.tableId).within(scores => {
        data.tableRows.forEach((elements, index) => {
          cy.wrap(scores).get('tr').eq(index).within(row => {
            cy.wrap(row).get('td').eq(0).should('have.text', elements);
          });
        });
      });
      cy.get('#' + data.tableId).scrollIntoView();
      cy.matchImageSnapshot('chd8-' + data.tableId);
    });
  });
});


export const geneData: any = [
  {
    geneSymbols: 'GRIN2B',
    genomicScores: [
      {
        category: 'autism_scores', name: 'Autism Scores', scores: [
          { name:'SFARI_gene_score', value: 1 }
        ]
      }, {
        category: 'protection_scores', name: 'Protection Scores', scores: [
          { name: 'RVIS_rank', value: 174.5 },
          { name: 'LGD_rank', value: 85.5 },
          { name: 'pLI_rank', value: 400 },
          { name: 'pRec_rank', value: 17792 }
        ]
      }
    ],
    geneSets: [
      {
        id: 'autism_gene_sets', name: 'Autism Gene Sets', scores: [
          { name: 'autism candidates from Iossifov PNAS 2015', value: true },
          { name: 'autism candidates from Sanders Neuron 2015', value: true }
        ]
      }, {
        id: 'relevant_gene_sets', name: 'Relevant Gene Sets', scores: [
          { name: 'CHD8 target genes', value:  false },
          { name: 'chromatin modifiers', value:  false },
          { name: 'essential genes', value:  true },
          { name: 'FMRP Darnell', value:  true }
        ]
      }
    ], datasets: [
      {
        name: 'iossifov_2014', columns: [
          'affected (2507)', 'unaffected (1910)'
        ], rows: [
          {
            variant_statistics: "LGDs", variant_ids: "denovo_lgds", affected: "3 (1.197)", unaffected: "–"
          },
          {
            variant_statistics: "missense", variant_ids: "denovo_missense", affected: "1 (0.399)", unaffected: "–"
          },
          {
            variant_statistics: "intron", variant_ids: "denovo_intron", affected: "–", unaffected: "–"
          }
        ]
      }
    ]
  }, {
    geneSymbols: 'POGZ',
    genomicScores: [
      {
        category: 'autism_scores', name: 'Autism Scores', scores: [
          { name:'SFARI_gene_score', value: 1 }
        ]
      }, {
        category: 'protection_scores', name: 'Protection Scores', scores: [
          { name: 'RVIS_rank', value: 565 },
          { name: 'LGD_rank', value: 1719.5 },
          { name: 'pLI_rank', value: 292 },
          { name: 'pRec_rank', value: 17913 }
        ]
      }
    ],
    geneSets: [
      {
        id: 'autism_gene_sets', name: 'Autism Gene Sets', scores: [
          { name: 'autism candidates from Iossifov PNAS 2015', value: true },
          { name: 'autism candidates from Sanders Neuron 2015', value: true }
        ]
      }, {
        id: 'relevant_gene_sets', name: 'Relevant Gene Sets', scores: [
          { name: 'CHD8 target genes', value:  true },
          { name: 'chromatin modifiers', value:  false },
          { name: 'essential genes', value:  false },
          { name: 'FMRP Darnell', value:  false }
        ]
      }
    ], datasets: [
      {
        name: 'iossifov_2014', columns: [
          'affected (2507)', 'unaffected (1910)'
        ], rows: [
          {
            variant_statistics: "LGDs", variant_ids: "denovo_lgds", affected: "2 (0.798)", unaffected: "–"
          },
          {
            variant_statistics: "missense", variant_ids: "denovo_missense", affected: "2 (0.798)", unaffected: "1 (0.524)"
          },
          {
            variant_statistics: "intron", variant_ids: "denovo_intron", affected: "–", unaffected: "–"
          }
        ]
      }
    ]
  }, {
    geneSymbols: 'CHD8',
    genomicScores: [
      {
        category: 'autism_scores', name: 'Autism Scores', scores: [
          { name:'SFARI_gene_score', value: 1 }
        ]
      }, {
        category: 'protection_scores', name: 'Protection Scores', scores: [
          { name: 'RVIS_rank', value: 193 },
          { name: 'LGD_rank', value: 83 },
          { name: 'pLI_rank', value: 31.5 },
          { name: 'pRec_rank', value: 18178 }
        ]
      }
    ],
    geneSets: [
      {
        id: 'autism_gene_sets', name: 'Autism Gene Sets', scores: [
          { name: 'autism candidates from Iossifov PNAS 2015', value: true },
          { name: 'autism candidates from Sanders Neuron 2015', value: true }
        ]
      }, {
        id: 'relevant_gene_sets', name: 'Relevant Gene Sets', scores: [
          { name: 'CHD8 target genes', value:  false },
          { name: 'chromatin modifiers', value:  true },
          { name: 'essential genes', value:  true },
          { name: 'FMRP Darnell', value:  true }
        ]
      }
    ], datasets: [
      {
        name: 'iossifov_2014', columns: [
          'affected (2507)', 'unaffected (1910)'
        ], rows: [
          {
            variant_statistics: "LGDs", variant_ids: "denovo_lgds", affected: "7 (2.792)", unaffected: "–"
          },
          {
            variant_statistics: "missense", variant_ids: "denovo_missense", affected: "–", unaffected: "–"
          },
          {
            variant_statistics: "intron", variant_ids: "denovo_intron", affected: "–", unaffected: "–"
          }
        ]
      }
    ]
  }
]

describe('data', () => {
  const page = new AutismGeneProfilesSingleView();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should compare all data in single view for GRIN2B', () => {
    page.openSingleView('GRIN2B');

    const geneSingleViewData = geneData.find(data => data.geneSymbols === 'GRIN2B');

    page.getGeneSymbols();
    cy.get('@geneSymbols').then(symbols => {
      expect(symbols).to.deep.equal(geneSingleViewData.geneSymbols, geneSingleViewData.geneSymbols + ' gene symbols');
    });

    page.getGeneSets();
    cy.get('@geneSets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewData.geneSets, geneSingleViewData.geneSymbols + ' gene sets');
    });

    page.getDatasetData();
    cy.get('@datasets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewData.datasets, geneSingleViewData.geneSymbols + ' single view datasets');
    });

    page.getGenomicScores();
    cy.get('@genomicScores').then(scores => {
      expect(scores).to.deep.equal(geneSingleViewData.genomicScores, geneSingleViewData.geneSymbols + ' single view genomic scores');
    });

  });

  it('should compare all data in single view for CHD8', () => {
    page.openSingleView('CHD8', true);

    const geneSingleViewData = geneData.find(data => data.geneSymbols === 'CHD8');

    page.getGeneSymbols();
    cy.get('@geneSymbols').then(symbols => {
      expect(symbols).to.deep.equal(geneSingleViewData.geneSymbols, geneSingleViewData.geneSymbols + ' gene symbols');
    });

    page.getGeneSets();
    cy.get('@geneSets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewData.geneSets, geneSingleViewData.geneSymbols + ' gene sets');
    });

    page.getDatasetData();
    cy.get('@datasets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewData.datasets, geneSingleViewData.geneSymbols + ' single view datasets');
    });

    page.getGenomicScores();
    cy.get('@genomicScores').then(scores => {
      expect(scores).to.deep.equal(geneSingleViewData.genomicScores, geneSingleViewData.geneSymbols + ' single view genomic scores');
    });
  });

  it('should compare all data in single view for POGZ', () => {
    page.openSingleView('POGZ', true);
    const geneSingleViewData = geneData.find(data => data.geneSymbols === 'POGZ');

    page.getGeneSymbols();
    cy.get('@geneSymbols').then(symbols => {
      expect(symbols).to.deep.equal(geneSingleViewData.geneSymbols, geneSingleViewData.geneSymbols + ' gene symbols');
    });

    page.getGeneSets();
    cy.get('@geneSets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewData.geneSets, geneSingleViewData.geneSymbols + ' gene sets');
    });

    page.getDatasetData();
    cy.get('@datasets').then(sets => {
      expect(sets).to.deep.equal(geneSingleViewData.datasets, geneSingleViewData.geneSymbols + ' single view datasets');
    });

    page.getGenomicScores();
    cy.get('@genomicScores').then(scores => {
      expect(scores).to.deep.equal(geneSingleViewData.genomicScores, geneSingleViewData.geneSymbols + ' single view genomic scores');
    });
  });
})