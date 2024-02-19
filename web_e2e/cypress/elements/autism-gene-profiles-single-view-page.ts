import { GenotypeBlockPage } from './genotype-block-page';
import { BasePage, sidenavPageLinks } from './utils';

export class AutismGeneProfilesSingleViewPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-gene-profiles-single-view');
  }

  public openSingleViewPage(geneSymbol: string): void {
    let baseUrl = Cypress.config().baseUrl;
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl.slice(0, -1);
    }
    const agpUrl = sidenavPageLinks.autismGeneProfiles;

    cy.visit(`${baseUrl}/${agpUrl}/${geneSymbol}`);
    this.window.find('gpf-histogram svg').should('be.visible');
  }

  public get header(): element {
    return cy.get('gpf-gene-profiles-single-view h2');
  }

  public get geneBrowserLink(): element {
    return cy.get('#gene-browser-link');
  }

  public get UCSCLink(): element {
    return cy.get('a.link-external-page').contains('UCSC genome browser');
  }

  public get geneCardsLink(): element {
    return cy.get('a.link-external-page').contains('GeneCards');
  }

  public get pubmedLink(): element {
    return cy.get('a.link-external-page').contains('Pubmed');
  }

  public get autismScoresTable(): element {
    return cy.get('#autism_scores');
  }

  public get protectionScoresTable(): element {
    return cy.get('#protection_scores');
  }

  public get singleScoreMarkers(): element {
    return cy.get('.single-score-marker');
  }

  public get geneAutismGeneSetsTable() : element {
    return cy.get('#autism_gene_sets');
  }

  public get geneRelevantGeneSetsTable(): element {
    return cy.get('#relevant_gene_sets');
  }

  public get datasetsTable(): element {
    return cy.get('.datasets-table');
  }

  public getGeneSymbols(): void {
    cy.get('h2').then(symbols => {
      cy.wrap(symbols.text()).as('geneSymbols');
    });
  }

  public getGenomicScores(id: string = null) {
    const genomicScores = [];

    cy.get((id !== null ? '#' + id + '-single-view' : 'div.ng-star-inserted >') + ' :nth-child(3) > table')
      .each((table_iteration, index) => {
        genomicScores[index] = {
          category: '', name: '', scores: []
        };

        cy.wrap(table_iteration).within(table => {
          cy.wrap(table).invoke('attr', 'id').then(id => {
            genomicScores[index].category = id;
          });

          cy.wrap(table).get('th').then(name => {
            genomicScores[index].name = name.text();
          });

          cy.wrap(table).get('tr').each((table_row, row_index) => {
            genomicScores[index].scores[row_index] = {
              name: '', value: null
            };

            cy.wrap(table_row).within(row => {
              cy.wrap(row).get('td').not('.ng-star-inserted').then(score_name => {
                genomicScores[index].scores[row_index].name = score_name.text();
              });

              cy.wrap(row).get('td.ng-star-inserted').within(score_values => {
                cy.wrap(score_values).get('g > text.small').then(score => {
                  genomicScores[index].scores[row_index].value = parseFloat(score.text());
                });
              });
            });
          });
        });
      });

    cy.wrap(genomicScores).as('genomicScores');
    return genomicScores;
  }

  public getGeneSets(id: string = null) {
    const geneSets: any = [];

    cy.get((id !== null ? '#' + id + '-single-view' : 'div.ng-star-inserted >') + ' :nth-child(4) > table')
      .each((table_iteration, index) => {
        cy.wrap(table_iteration).within(table => {
          geneSets[index] = {
            id: null, name: null, scores: [
            ]
          };

          cy.wrap(table).invoke('attr', 'id').then(id => {
            geneSets[index]['id'] = id; // sets the id
          });
          cy.wrap(table).get('th').then(tableName => {
            geneSets[index]['name'] = tableName.text();
          });

          cy.wrap(table).get('tr').each((row, rowIndex) => {
            cy.wrap(row).within(el => {
              geneSets[index]['scores'][rowIndex] = {
                name: '',
                value: false
              };

              cy.wrap(el).get('td').eq(0).then(name => {
                geneSets[index]['scores'][rowIndex]['name'] = name.text();
              });
              cy.wrap(el).get('td').eq(1).then(value => {
                cy.wrap(value).within(el => {
                  if (el.text() === 'check') {
                    geneSets[index]['scores'][rowIndex]['value'] = true;
                  }
                });
              });
            });
          });
        });
      });
    cy.wrap(geneSets).as('geneSets');

    return geneSets;
  }

  public getDatasetData(id: string = null) {
    const datasets = [];

    cy.get((id !== null ? '#' + id + '-single-view' : 'div.ng-star-inserted >') + ' :nth-child(5) > table')
      .each((table_iterator, index) => {
        datasets[index] = {
          name: '', columns: [], rows: [
            {
              variant_statistics: '', variant_ids: '', affected: '', unaffected: ''
            }
          ]
        };
        cy.wrap(table_iterator).within(table => {
          cy.wrap(table).get('thead > :nth-child(1) > th > span').then(name => {
            datasets[index].name = name.text();
          });

          cy.wrap(table).get('thead > :nth-child(2) > th.ng-star-inserted').each((column, column_index) => {
            datasets[index].columns[column_index] = column.text();
          });

          cy.wrap(table).get('tbody > tr').each((table_row, table_index) => {
            datasets[index].rows[table_index] = {
              variant_statistics: '', variant_ids: '', affected: '', unaffected: ''
            };
            cy.wrap(table_row).within(row => {
              cy.wrap(row).invoke('attr', 'id').then(id => {
                datasets[index].rows[table_index].variant_ids = id;
              });
              cy.wrap(row).get('td').not('.ng-star-inserted').then(name => {
                datasets[index].rows[table_index].variant_statistics = name.text();
              });
              cy.wrap(row).get('td').eq(1).then(affected => {
                if (affected.text() !== 'remove') {
                  datasets[index].rows[table_index].affected = affected.text();
                } else {
                  datasets[index].rows[table_index].affected = '–';
                }
              });
              cy.wrap(row).get('td').eq(2).then(unaffected => {
                if (unaffected.text() !== 'remove') {
                  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
                  datasets[index].rows[table_index].unaffected = unaffected.text();
                } else {
                  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
                  datasets[index].rows[table_index].unaffected = '–';
                }
              });
            });
          });
        });
      });

    cy.wrap(datasets).as('datasets');

    return datasets;
  }

  public getStudyExpectedDataFromGenotype(variantStatistics): void {
    const genotypeBlockPage = new GenotypeBlockPage();

    const studyWrapper = {
      denovo_lgds: genotypeBlockPage.effectTypesGroups.get('LGDs'),
      denovo_missense: ['missense'],
      denovo_intron: ['intron']
    };
    const effectModelFromGenotypeWrapper = new Map<string, string>();
    for (const value in studyWrapper) {
      effectModelFromGenotypeWrapper.set(value, studyWrapper[value]);
    }

    cy.wrap(effectModelFromGenotypeWrapper.get(variantStatistics)).as('genotypeExpectedWrapper');
  }

  public getStudyActualDataFromGenotype(): void {
    const selectedEffects = [];

    cy.get('.effect-card > .card-block label').each(label => {
      cy.wrap(label).within(checkBox => {
        cy.wrap(checkBox).get('input').then(check => {
          cy.wrap(check).invoke('prop', 'checked').then(isCheck => {
            if (isCheck === true) {
              selectedEffects.push(label.text());
            }
          });
        });
      });
    });

    cy.wrap(selectedEffects).as('genotypeActualWrapper');
  }
}
