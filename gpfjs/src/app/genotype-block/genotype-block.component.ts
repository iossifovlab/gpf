import { Component, Input, OnChanges } from '@angular/core';
import { Dataset } from '../datasets/datasets';

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css'],
})
export class GenotypeBlockComponent implements OnChanges {
  @Input()
  dataset: Dataset;

  inheritanceTypes: Set<string>;
  selectedInheritanceTypes: Set<string>;

  constructor() { }

  ngOnChanges() {
    this.inheritanceTypes = new Set(this.dataset.genotypeBrowserConfig.inheritanceTypeFilter);
    this.selectedInheritanceTypes = new Set(this.dataset.genotypeBrowserConfig.selectedInheritanceTypeFilterValues);
  }
}
