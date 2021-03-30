import { BaseController } from "./base-controller";
import { EffecttypesPage } from "./effectypes-page";
import { FamilyFilterBlockPage } from "./family-filter-block-page";
import { GenesBlockPage } from "./genes-block-page";
import { GenotypeBlockPage } from "./genotype-block-page";
import { GenotypeBrowserPage } from "./genotype-browser-page";
import { RegionsBlockPage } from "./regions-block-page";

export class GenotypeBrowserController extends BaseController {
  genotypeBrowserPage = new GenotypeBrowserPage();
  genotypeBlockPage = new GenotypeBlockPage();
  genesBlockPage = new GenesBlockPage();
  regionsBlockPage = new RegionsBlockPage();
  familyFilterBlockPage = new FamilyFilterBlockPage();

  setStudy(study: string) {
    this.genotypeBrowserPage.navigateToDatasetPage(study, 'Genotype Browser');
  }

  private navigateToAffectedStatus() {
    this.genotypeBlockPage.pedigreeDropdownMenuButton.click();
    this.genotypeBlockPage.getPedigreeDropdownOptionByText('Affected Status').click();
  }

  private navigateToRoles() {
    this.genotypeBlockPage.pedigreeDropdownMenuButton.click();
    this.genotypeBlockPage.getPedigreeDropdownOptionByText('Role').click();
  }

  setAffectedStatusToAll() {
    this.navigateToAffectedStatus();
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
  }

  setAffectedStatusToNone() {
    this.navigateToAffectedStatus();
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
  }

  setAffectedStatus(affectedStatus: string) {
    this.navigateToAffectedStatus();
    this.setAffectedStatusToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', affectedStatus).click();
  }

  setRolesToAll() {
    this.navigateToRoles();
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
  }

  setRolesToNone() {
    this.navigateToRoles();
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
  }

  setRoles(roles: string[]) {
    this.setRolesToNone();
    for (const role of roles) {
      this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', role).click();
    }
  }

  setEffectTypesToNone() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'None').click();
  }

  setEffectTypes(effectTypes: string[]) {
    this.setEffectTypesToNone();
    for (const effectType of effectTypes) {
      this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-effecttypes', effectType).click();
    }
  }

  setEffectTypesGroup(group: string) {
    this.setEffectTypes(this.genotypeBlockPage.effectTypesGroups.get(group));
  }

  setPhenotypeToAll() {
    cy.get('gpf-pedigree-selector').contains('Phenotype').should('exist');
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
  }

  setPhenotypeToNone() {
    cy.get('gpf-pedigree-selector').contains('Phenotype').should('exist');
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
  }

  setPhenotype(phenotype: string) {
    this.setPhenotypeToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', phenotype).click();
  }

  setPresentInChildToAll() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'All').click();
  }

  setPresentInChildToNone() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'None').click();
  }

  setPresentInChild(child: string) {
    this.setPresentInChildToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-present-in-child', child).click();
  }

  setPresentInParentToAll() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'All').click();
  }

  setPresentInParentToNone() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'None').click();
  }

  setPresentInParent(parent: string) {
    this.setPresentInParentToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-present-in-parent', parent).click();
  }

  setGendersToAll() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'All').click();
  }

  setGendersToNone() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'None').click();
  }

  setGender(gender: string) {
    this.setGendersToNone();
    cy.get('gpf-gender span.gender-icon.' + gender).click();
  }

  setVariantTypesToAll() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'All').click();
  }

  setVariantTypesToNone() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'None').click();
  }

  setVariantType(variantType: string) {
    this.setVariantTypesToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-varianttypes', variantType).click();
  }

  setInheritanceTypeToAll() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'All').click();
  }

  setInheritanceTypeToNone() {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'None').click();
  }

  setInheritanceType(inheritanceType: string) {
    this.setInheritanceTypeToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-inheritancetypes', inheritanceType).click();
  }
  // // Add genomic score filter

  // // Remove genomic score filter

  setFamilyFilterToAll() {
    this.genotypeBrowserPage.findButtonInComponentContainingText('gpf-family-filters-block', 'All').click();
  }

  setFamilyFilterToId(id: string) {
    this.familyFilterBlockPage.familyIdsButton.click();
    this.familyFilterBlockPage.familyIdsTextarea.type(id);
  }

  filterGenesByAll() {
    this.genesBlockPage.allButton.click();
  }

  filterGenesByGeneSymbol(symbol: string) {
    this.genesBlockPage.geneSymbolsButton.click();
    this.genesBlockPage.geneSymbolsTextarea.type(symbol);
  }

  filterGenesByGeneSets(collection: string, set: string) {
    this.genesBlockPage.geneSetsButton.click();
    this.genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(collection);

    this.genesBlockPage.geneSetsSearchbox.click();
    this.genesBlockPage.geneSetsSearchbox.type(set);
    this.genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(set).click();
  }

  setRegion(region: string) {
    this.regionsBlockPage.regionsFilterButton.click();
    this.regionsBlockPage.regionsFilterTextarea.type(region);
  }

  showTablePreview() {
    cy.wait(500);
    this.genotypeBrowserPage.tablePreviewButton.click();
  }

  // // Share query

  // // Save query
}