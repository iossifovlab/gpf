import { BasePage } from './utils';

export class GenotypeBlockPage extends BasePage {
  public effectTypesGroups = new Map([
    ['All', [
      'Nonsense',
      'Frame-shift',
      'Splice-site',
      'No-frame-shift-newStop',
      'Missense',
      'No-frame-shift',
      'noStart',
      'noEnd',
      'Synonymous',
      'Non coding',
      'Intron',
      'Intergenic',
      '3\'-UTR',
      '5\'-UTR'
    ]],
    ['None', []],
    ['LGDs', [
      'Nonsense',
      'Frame-shift',
      'Splice-site',
      'No-frame-shift-newStop'
    ]],
    ['Nonsynonymous', [
      'Nonsense',
      'Frame-shift',
      'Splice-site',
      'No-frame-shift-newStop',
      'Missense',
      'No-frame-shift',
      'noStart',
      'noEnd'
    ]],
    ['Coding', [
      'Nonsense',
      'Frame-shift',
      'Splice-site',
      'No-frame-shift-newStop',
      'Missense',
      'No-frame-shift',
      'noStart',
      'noEnd',
      'Synonymous'
    ]],
    ['UTRs', [
      '3\'-UTR',
      '5\'-UTR'
    ]]
  ]);

  public get window(): element {
    return cy.get('gpf-genotype-block');
  }

  // This function is also used for the child gender block
  public findCheckboxInComponentContainingText(componentSelector: string, text: string): element {
    if (componentSelector !== 'gpf-gender') {
      const exactTextRegex = new RegExp(`^${text}$`);
      return cy.get(componentSelector + ' div.checkbox label').contains(exactTextRegex);
    } else if (componentSelector === 'gpf-gender') {
      return cy.get('.gender-icon ' + text).parent().get('input');
    }
  }

  public findAllCheckboxesInComponent(componentSelector: string): element {
    return cy.get(componentSelector + ' input');
  }

  public get pedigreeDropdownMenuButton(): element {
    return cy.get('gpf-genotype-block button#pedigree-dropdown-menu-button');
  }

  public get pedigreeDropdownMenu(): element {
    return cy.get('gpf-genotype-block gpf-pedigree-selector .dropdown-menu');
  }

  public getPedigreeDropdownOptionByText(text: string): element {
    return cy.get('gpf-genotype-block gpf-pedigree-selector a').contains(text);
  }
}
