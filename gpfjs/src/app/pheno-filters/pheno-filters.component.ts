import { Component, OnInit, Input } from '@angular/core';
import { PhenoFilter } from '../datasets/datasets';

@Component({
  selector: 'gpf-pheno-filters',
  templateUrl: './pheno-filters.component.html',
  styleUrls: ['./pheno-filters.component.css']
})
export class PhenoFiltersComponent implements OnInit {
  @Input() phenoFilters: Array<PhenoFilter>;


  constructor() { }

  ngOnInit() {
  }

  get categoricalPhenoFilters() {
    if (!this.phenoFilters) {
      return null;
    }
    
    return this.phenoFilters.filter(
      (phenoFilter: PhenoFilter) => phenoFilter.measureType == 'categorical'
    );
  }

}
