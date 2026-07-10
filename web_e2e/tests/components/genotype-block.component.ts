import { Locator, Page } from '@playwright/test';
import { EffectTypes } from './effect-types.component';
import { VariantTypes } from './variant-types.component';
import { InheritanceTypes } from './inheritance-types.component';
import { Gender } from './gender.component';
import { PedigreeSelector } from './pedigree-selector.component';
import { PresentInChild } from './present-in-child.component';
import { ZygosityFilters } from './zygosity-filters.component';

// Component object for the `gpf-genotype-block` widget, composing the
// individual genotype filters.
export class GenotypeBlock {
  public readonly root: Locator;
  public readonly effectTypes: EffectTypes;
  public readonly variantTypes: VariantTypes;
  public readonly inheritanceTypes: InheritanceTypes;
  public readonly gender: Gender;
  public readonly pedigreeSelector: PedigreeSelector;
  public readonly presentInChild: PresentInChild;
  public readonly zygosity: ZygosityFilters;

  public constructor(private readonly page: Page) {
    this.root = page.locator('gpf-genotype-block');
    this.effectTypes = new EffectTypes(page);
    this.variantTypes = new VariantTypes(page);
    this.inheritanceTypes = new InheritanceTypes(page);
    this.gender = new Gender(page);
    this.pedigreeSelector = new PedigreeSelector(page);
    this.presentInChild = new PresentInChild(page);
    this.zygosity = new ZygosityFilters(page);
  }
}
