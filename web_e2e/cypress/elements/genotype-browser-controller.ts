import { BaseController } from "./base-controller";
import { FamilyFilterBlockPage } from "./family-filter-block-page";
import { GenesBlockPage } from "./genes-block-page";
import { GenotypeBlockPage } from "./genotype-block-page";
import { GenotypeBrowserPage } from "./genotype-browser-page";
import { RegionsBlockPage } from "./regions-block-page";
import { toolPageLinks } from "./utils";

export class GenotypeBrowserController extends BaseController {
  private genotypeBrowserPage = new GenotypeBrowserPage();
  private genotypeBlockPage = new GenotypeBlockPage();
  private genesBlockPage = new GenesBlockPage();
  private regionsBlockPage = new RegionsBlockPage();
  private familyFilterBlockPage = new FamilyFilterBlockPage();

  public setStudy(study: string): void {
    this.genotypeBrowserPage.navigateToDatasetPage(study, toolPageLinks.genotypeBrowser);
  }

  private navigateToAffectedStatus(): void {
    this.genotypeBlockPage.pedigreeDropdownMenuButton.click();
    this.genotypeBlockPage.getPedigreeDropdownOptionByText('Affected Status').click();
  }

  private navigateToRoles(): void {
    this.genotypeBlockPage.pedigreeDropdownMenuButton.click();
    this.genotypeBlockPage.getPedigreeDropdownOptionByText('Role').click();
  }

  // public setAffectedStatusToAll(): void {
  //   this.navigateToAffectedStatus();
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
  // }

  private setAffectedStatusToNone(): void {
    this.navigateToAffectedStatus();
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
  }

  public setAffectedStatus(affectedStatus: string): void {
    this.navigateToAffectedStatus();
    this.setAffectedStatusToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', affectedStatus).click();
  }

  // public setRolesToAll(): void {
  //   this.navigateToRoles();
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
  // }

  private setRolesToNone(): void {
    this.navigateToRoles();
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
  }

  private setRoles(roles: string[]): void {
    this.setRolesToNone();
    for (const role of roles) {
      this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', role).click();
    }
  }

  private setEffectTypesToNone(): void {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'None').click();
  }

  public setEffectTypes(effectTypes: string[]): void {
    this.setEffectTypesToNone();
    for (const effectType of effectTypes) {
      this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-effect-types', effectType).click();
    }
  }

  public setEffectTypesGroup(group: string): void {
    this.setEffectTypes(this.genotypeBlockPage.effectTypesGroups.get(group));
  }

  public setEffectTypesToAll(): void {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();
  }

  // public setPhenotypeToAll(): void {
  //   cy.get('gpf-pedigree-selector').contains('Phenotype').should('exist');
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
  // }

  private setPhenotypeToNone(): void {
    cy.get('gpf-pedigree-selector').contains('Phenotype').should('exist');
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
  }

  private setPhenotype(phenotype: string): void {
    this.setPhenotypeToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', phenotype).click();
  }

  // public setPresentInChildToAll(): void {
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'All').click();
  // }

  private setPresentInChildToNone(): void {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'None').click();
  }

  private setPresentInChild(child: string): void {
    this.setPresentInChildToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-present-in-child', child).click();
  }

  // public setPresentInParentToAll(): void {
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'All').click();
  // }

  private setPresentInParentToNone(): void {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'None').click();
  }

  private setPresentInParent(parent: string): void {
    this.setPresentInParentToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-present-in-parent', parent).click();
  }

  // public setGendersToAll(): void {
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'All').click();
  // }

  private setGendersToNone(): void {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'None').click();
  }

  public setGender(gender: string): void {
    this.setGendersToNone();
    cy.get('gpf-gender span.gender-icon.' + gender).click();
  }

  // public setVariantTypesToAll(): void {
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-variant-types', 'All').click();
  // }

  private setVariantTypesToNone(): void {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-variant-types', 'None').click();
  }

  public setVariantType(variantType: string): void {
    this.setVariantTypesToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-variant-types', variantType).click();
  }

  // public setInheritanceTypeToAll(): void {
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'All').click();
  // }

  private setInheritanceTypeToNone(): void {
    this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'None').click();
  }

  public setInheritanceType(inheritanceType: string): void {
    this.setInheritanceTypeToNone();
    this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-inheritancetypes', inheritanceType).click();
  }

  // public setFamilyFilterToAll(): void {
  //   this.genotypeBrowserPage.findButtonInComponentContainingText('gpf-family-filters-block', 'All').click();
  // }

  public setFamilyFilterToId(id: string): void {
    this.familyFilterBlockPage.familyIdsButton.click();
    this.familyFilterBlockPage.familyIdsTextarea.type(id);
  }

  public filterGenesByAll(): void {
    this.genesBlockPage.allButton.click();
  }

  public filterGenesByGeneSymbol(symbol: string): void {
    this.genesBlockPage.geneSymbolsButton.click();
    this.genesBlockPage.geneSymbolsTextarea.type(symbol);
  }

  public filterGenesByGeneSets(collection: string, set: string): void {
    this.genesBlockPage.geneSetsButton.click();
    this.genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(collection, {force: true});

    this.genesBlockPage.geneSetsSearchbox.click();
    this.genesBlockPage.geneSetsSearchbox.type(set);
    this.genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(set).click();
  }

  public setRegion(region: string): void {
    this.regionsBlockPage.regionsFilterButton.click();
    this.regionsBlockPage.regionsFilterTextarea.should('not.be.disabled');
    this.regionsBlockPage.regionsFilterTextarea.type(region);
  }

  public showTablePreview(): void {
    this.genotypeBrowserPage.tablePreviewButton.click();
  }
}