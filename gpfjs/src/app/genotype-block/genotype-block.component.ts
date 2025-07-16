import { Component, Input, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';

@Component({
    selector: 'gpf-genotype-block',
    templateUrl: './genotype-block.component.html',
    styleUrls: ['./genotype-block.component.css'],
    standalone: false
})
export class GenotypeBlockComponent implements OnInit {
  @Input() public dataset: Dataset;
  public variantTypesSet = new Set<string>();
  public selectedVariantTypesSet = new Set<string>();
  public inheritanceTypeFilterSet = new Set<string>();
  public selectedInheritanceTypeFilterValuesSet = new Set<string>();

  public ngOnInit(): void {
    this.variantTypesSet = new Set(this.dataset.genotypeBrowserConfig.variantTypes);
    this.selectedVariantTypesSet = new Set(this.dataset.genotypeBrowserConfig.selectedVariantTypes);
    this.inheritanceTypeFilterSet = new Set(this.dataset.genotypeBrowserConfig.inheritanceTypeFilter);
    this.selectedInheritanceTypeFilterValuesSet =
      new Set(this.dataset.genotypeBrowserConfig.selectedInheritanceTypeFilterValues);
  }
}
