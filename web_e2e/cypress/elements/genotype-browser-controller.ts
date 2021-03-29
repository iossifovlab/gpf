import { BaseController } from "./base-controller";
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
    console.log(effectTypes);
    this.setEffectTypesToNone();
    for (const effectType of effectTypes) {
      this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-effecttypes', effectType).click();
    }
  }

  setEffectTypesGroup(group: string) {
    this.setEffectTypes(this.genotypeBlockPage.effectTypesGroups.get(group));
  }

  // setPhenotypeToAll() {
  //   if ((element(by.cssContainingText('gpf-pedigree-selector', 'Phenotype'))).isPresent()) {
  //     this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //       this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All')
  //     );
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();

  //     this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-pedigree-selector').each((checkbox) => {
  //       browser.driver.wait(() => {
  //         return checkbox.isSelected() === true;
  //       }, 35000);
  //     });
  //   }
  // }

  // setPhenotypeToNone() {
  //   if ((element(by.cssContainingText('gpf-pedigree-selector', 'Phenotype'))).isPresent()) {
  //     this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //       this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None')
  //     );
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();

  //     this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-pedigree-selector').each((checkbox) => {
  //       browser.driver.wait(() => {
  //         return checkbox.isSelected() === false;
  //       }, 35000);
  //     });
  //   }
  // }

  // setPhenotype(phenotype: string) {
  //   this.setPhenotypeToNone();
  //   if ((element(by.cssContainingText('gpf-pedigree-selector', 'Phenotype'))).isPresent()) {
  //     const checkbox = this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-pedigree-selector', phenotype);
  //     this.genotypeBrowserPage.browserWaitForVisibilityOfElement(checkbox);
  //     checkbox.click();

  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === true;
  //     }, 35000);
  //   }
  // }

  // setPresentInChildToAll() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'All')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'All').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-present-in-child').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === true;
  //     }, 35000);
  //   });
  // }

  // setPresentInChildToNone() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'None')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-child', 'None').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-present-in-child').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === false;
  //     }, 35000);
  //   });
  // }

  // setPresentInChild(child: string) {
  //   this.setPresentInChildToNone();
  //   const checkbox = this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-present-in-child', child);
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(checkbox);
  //   checkbox.click();

  //   browser.driver.wait(() => {
  //     return checkbox.isSelected() === true;
  //   }, 35000);
  // }

  // setPresentInParentToAll() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'All')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'All').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-present-in-parent').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === true;
  //     }, 35000);
  //   });
  // }

  // setPresentInParentToNone() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'None')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-present-in-parent', 'None').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-present-in-parent').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === false;
  //     }, 35000);
  //   });
  // }

  // setPresentInParent(parent: string) {
  //   this.setPresentInParentToNone();
  //   const checkbox = this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-present-in-parent', parent);
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(checkbox);
  //   checkbox.click();

  //   browser.driver.wait(() => {
  //     return checkbox.isSelected() === true;
  //   }, 35000);
  // }

  // setGendersToAll() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'All')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'All').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-gender').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === true;
  //     }, 35000);
  //   });
  // }

  // setGendersToNone() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'None')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'None').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-gender').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === false;
  //     }, 35000);
  //   });
  // }

  // setGender(gender: string) {
  //   this.setGendersToNone();
  //   const icon = element(by.css('gpf-gender span.gender-icon.' + gender));
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(icon);
  //   icon.click();

  //   browser.driver.wait(() => {
  //     return icon.element(by.xpath('..')).element(by.css('input')).isSelected() === true;
  //   }, 35000);
  // }

  // setVariantTypesToAll() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'All')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'All').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-varianttypes').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === true;
  //     }, 35000);
  //   });
  // }

  // setVariantTypesToNone() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'None')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'None').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-varianttypes').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === false;
  //     }, 35000);
  //   });
  // }

  // setVariantType(variantType: string) {
  //   this.setVariantTypesToNone();
  //   const checkbox = this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-varianttypes', variantType);
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(checkbox);
  //   checkbox.click();

  //   browser.driver.wait(() => {
  //     return checkbox.isSelected() === true;
  //   }, 35000);
  // }

  // setInheritanceTypeToAll() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'All')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'All').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-inheritancetypes').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === true;
  //     }, 35000);
  //   });
  // }

  // setInheritanceTypeToNone() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'None')
  //   );
  //   this.genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'None').click();

  //   this.genotypeBlockPage.findAllCheckboxesInComponent('gpf-inheritancetypes').each((checkbox) => {
  //     browser.driver.wait(() => {
  //       return checkbox.isSelected() === false;
  //     }, 35000);
  //   });
  // }

  // setInheritanceType(inheritanceType: string) {
  //   this.setInheritanceTypeToNone().then(() => {
  //       const checkbox = this.genotypeBlockPage.findCheckboxInComponentContainingText('gpf-inheritancetypes', inheritanceType);
  //       this.genotypeBrowserPage.browserWaitForVisibilityOfElement(checkbox);
  //       checkbox.click();

  //       browser.driver.wait(() => {
  //         return checkbox.isSelected() === true;
  //       }, 35000);
  //   });

  // }

  // // Add genomic score filter

  // // Remove genomic score filter

  // setFamilyFilterToAll() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genotypeBrowserPage.findButtonInComponentContainingText('gpf-family-filters-block', 'All')
  //   );
  //   this.genotypeBrowserPage.findButtonInComponentContainingText('gpf-family-filters-block', 'All').click();
  // }

  // setFamilyFilterToId(id: string) {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.familyFilterBlockPage.familyIdsButton);
  //   this.familyFilterBlockPage.familyIdsButton.click();
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.familyFilterBlockPage.familyIdsTextarea);
  //   this.familyFilterBlockPage.familyIdsTextarea.sendKeys(id);
  // }

  // filterGenesByAll() {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.genesBlockPage.allButton);
  //   this.genesBlockPage.allButton.click();
  // }

  filterGenesByGeneSymbol(symbol: string) {
    this.genesBlockPage.geneSymbolsButton.click();
    this.genesBlockPage.geneSymbolsTextarea.type(symbol);
  }

  // filterGenesByGeneSets(collection: string, set: string) {
  //   this.genesBlockPage.browserWaitForVisibilityOfElement(this.genesBlockPage.geneSetsButton);
  //   this.genesBlockPage.geneSetsButton.click();
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.genesBlockPage.geneSetsPanel);
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.genesBlockPage.geneSetsCollectionSelectorDropdownMenu);
  //   this.genesBlockPage.geneSetsCollectionSelectorDropdownMenu.click();
  //   this.genesBlockPage.browserWaitForVisibilityOfElement(
  //     this.genesBlockPage.findGeneSetsCollectionOptionByText(collection)
  //   );
  //   this.genesBlockPage.findGeneSetsCollectionOptionByText(collection).click();

  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.genesBlockPage.geneSetsSearchbox);
  //   this.genesBlockPage.geneSetsSearchbox.click();
  //   this.genesBlockPage.geneSetsSearchbox.sendKeys(set);
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(
  //     this.genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(set)
  //   );
  //   this.genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(set).click();
  // }

  // setRegion(region: string) {
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.regionsBlockPage.regionsFilterButton);
  //   this.regionsBlockPage.regionsFilterButton.click();
  //   this.genotypeBrowserPage.browserWaitForVisibilityOfElement(this.regionsBlockPage.regionsFilterTextarea);
  //   this.regionsBlockPage.regionsFilterTextarea.sendKeys(region);
  // }

  showTablePreview() {
    cy.wait(500);
    this.genotypeBrowserPage.tablePreviewButton.click();
  }

  // // Share query

  // // Save query
}