import { BasePage } from './utils';

export class GenesBlockPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-genes-block');
  }

  public get allButton(): element {
    return cy.get('gpf-genes-block a').contains('All');
  }

  public get geneSymbolsButton(): element {
    return cy.get('#gene-symbols');
  }

  public get geneSymbolsPanel(): element {
    return cy.get('#gene-symbols-panel');
  }

  public get geneSymbolsTextarea(): element {
    return cy.get('gpf-gene-symbols textarea');
  }

  public get geneSetsButton(): element {
    return cy.get('#gene-sets');
  }

  public get geneSetsPanel(): element {
    return cy.get('#gene-sets-panel');
  }

  public get geneSetsSearchbox(): element {
    return cy.get('#search-box');
  }

  public findGeneSetsSearchboxDropdownOptionsByText(text: string): element {
    return cy.get('button.dropdown-item span').contains(text);
  }

  public get firstGeneSetFromDropdownMenu(): element {
    return cy.get('button.dropdown-item span').first();
  }

  public get selectedGeneSet(): element {
    return cy.get('#selected-value');
  }

  public get geneSetCountElement(): element {
    return cy.get('gpf-gene-sets > div > div div.ng-star-inserted').contains('Count');
  }

  public get downloadButton(): element {
    return cy.get('gpf-gene-sets a').contains('Download');
  }

  public get geneSetsCollectionSelectorDropdownMenu(): element {
    return cy.get('gpf-gene-sets select.form-control');
  }

  public get geneWeightsButton(): element {
    return cy.get('#gene-weights');
  }

  public get genesWeightsPanel(): element {
    return cy.get('#gene-weights-panel');
  }

  public findDenovoGeneSetCollectionCheckbox(genotypeDataId: string, peopleGroupValue: string): element {
    const checkboxId: string = genotypeDataId + '-checkbox-' + peopleGroupValue;
    return cy.get(`#${checkboxId}`);
  }
}
