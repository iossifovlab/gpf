import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
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
    page.geneBrowserLink.should('have.text', 'View CHD8 in the Gene Browser');
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
/*
  it('should display SFARI link when is contained in the list', () => {
  });
  // add tests for SFARI link - it had a specific condition in order to be displayed,
  // see if that logic works
  // it('should display SFARI link when ... and not display it when ...', () => {
  // });
  // it('should have the correct href for the SFARI link', () => {
  // }); */

  it.only('should have proper single view data', () => {
    //page.cleanup();
    //page.navigateToHome();
    //page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
    const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type('GRIN2B');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=GRIN2B&sortBy=autism_gene_sets_rank&order=desc').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView('GRIN2B');
    //autismGeneProfilesTablePage.allTableCells.first().click();

    page.compareData(gene_data);
  });

  it.skip('should have proper single view links in the study table', () => {
    page.cleanup();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);

    const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
    page.autismGeneToolAllView.click();
    autismGeneProfilesTablePage.geneSearchInput.clear().type('GRIN2B');
    cy.intercept('GET', '/gpf/api/v3/autism_gene_tool/genes/?page=1&symbol=GRIN2B&sortBy=autism_gene_sets_rank&order=desc').as('responseHandler');
    cy.wait('@responseHandler');
    autismGeneProfilesTablePage.allTableRows.first().should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
    page.getView('GRIN2B');

    gene_data.statistics.study.affected.forEach(arr => {
      page.datasetsTable.within(el => {
        if(arr === '' || arr === '–') {

        } else {
          cy.wrap(el).contains(arr).invoke('attr', 'href').then(href => {
            console.log(href);
            //cy.visit(href);
          });
        }
      });
    });

  });
});

const gene_data = {
  gene_symbols: 'GRIN2B',
  data: [
    { name:'SFARI_gene_score', value: 1 }, // sfari_score: 
    { name: 'RVIS_rank',value: 174.5 },  // rvis_rank: 
    { name: 'LGD_rank',value: 85.5 }, // lgd_rank:
    { name: 'pLI_rank',value: 400 }, // pli_rank: 
    { name: 'pRec_rank',value: 17792 } // prec_rank: 
  ], statistics: {
    autism_gene_sets: [
      { name: 'autism candidates from Iossifov PNAS 2015', value: true },
      { name: 'autism candidates from Sanders Neuron 2015', value: true }
    ], relevant_gene_sets: [
      { name: 'CHD8 target genes', value:  false },
      { name: 'chromatin modifiers', value:  true },
      { name: 'essential genes', value:  true },
      { name: 'FMRP Darnell', value:  true }
    ], study: {
      variant_statistics: ['', '', ''],
      affected: ['3 (1.197)', '1 (0.399)', '–'],
      unaffected: ['–', '–', '–']
    }
  }
}


const sfari_genes = [
  'ABCA7',
  'ACE',
  'ACHE',
  'ARHGEF10',
  'BICRA',
  'BICDL1',
  'BRINP3',
  'BST1'
];

