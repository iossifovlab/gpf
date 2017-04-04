import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { PhenoFilter } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { Store } from '@ngrx/store';
import {
  PhenoFiltersState, PHENO_FILTERS_INIT
} from './pheno-filters';
import { Observable } from 'rxjs/Observable';
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-pheno-filters',
  templateUrl: './pheno-filters.component.html',
  styleUrls: ['./pheno-filters.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => PhenoFiltersComponent) }]
})
export class PhenoFiltersComponent extends QueryStateCollector implements OnInit {
  @Input() phenoFilters: Array<PhenoFilter>;
  @Input() datasetId: string;

private PhenoFiltersState: Observable<[PhenoFiltersState, boolean, ValidationError[]]>;

  constructor(
    private store: Store<any>
  ) {
    super();
    this.PhenoFiltersState = toObservableWithValidation(PhenoFiltersState, this.store.select('phenoFilters'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': PHENO_FILTERS_INIT,
    });
  }

  get categoricalPhenoFilters() {
    if (!this.phenoFilters) {
      return null;
    }

    return this.phenoFilters.filter(
      (phenoFilter: PhenoFilter) => phenoFilter.measureType == 'categorical'
    );
  }

  get continuousPhenoFilters() {
    if (!this.phenoFilters) {
      return null;
    }

    return this.phenoFilters.filter(
      (phenoFilter: PhenoFilter) => phenoFilter.measureType == 'continuous'
    );
  }

}
