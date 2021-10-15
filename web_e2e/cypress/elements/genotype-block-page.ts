import { BasePage } from './utils';

export class GenotypeBlockPage extends BasePage {
  effectTypesGroups = new Map([
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
      'No-frame-shift-newStop',
    ]],
    ['Nonsynonymous', [
      'Nonsense',
      'Frame-shift',
      'Splice-site',
      'No-frame-shift-newStop',
      'Missense',
      'No-frame-shift',
      'noStart',
      'noEnd',
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
      'Synonymous',
    ]],
    ['UTRs', [
      '3\'-UTR',
      '5\'-UTR'
    ]],
  ]);

  get window() {
    return cy.get('gpf-genotype-block');
  }

  // This function is also used for the child gender block
  findCheckboxInComponentContainingText(componentSelector: string, text: string) {
    if (componentSelector !== 'gpf-gender') {
      const exactTextRegex = new RegExp(`^${text}$`);
      return cy.get(componentSelector + ' div.checkbox label').contains(exactTextRegex);
    } else if (componentSelector === 'gpf-gender') {
      return cy.get('.gender-icon ' + text).parent().get('input');
    }
  }

  findAllCheckboxesInComponent(componentSelector: string) {
    return cy.get(componentSelector + ' input');
  }

  get pedigreeDropdownMenuButton() {
    return cy.get('gpf-genotype-block button#pedigree-dropdown-menu-button');
  }

  get pedigreeDropdownMenu() {
    return cy.get('gpf-genotype-block gpf-pedigree-selector .dropdown-menu');
  }

  getPedigreeDropdownOptionByText(text: string) {
    return cy.get('gpf-genotype-block gpf-pedigree-selector a').contains(text);
  }
}
