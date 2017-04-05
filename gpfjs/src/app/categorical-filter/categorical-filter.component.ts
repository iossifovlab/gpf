import { Component, OnInit, Input } from '@angular/core';
import { Store } from '@ngrx/store';
import {
  PhenoFiltersState, CategoricalFilterState, PHENO_FILTERS_ADD_CATEGORICAL,
  PHENO_FILTERS_CATEGORICAL_SET_SELECTION
} from '../pheno-filters/pheno-filters';
import { Observable } from 'rxjs/Observable';

@Component({
  selector: 'gpf-categorical-filter',
  templateUrl: './categorical-filter.component.html',
  styleUrls: ['./categorical-filter.component.css']
})
export class CategoricalFilterComponent implements OnInit {
  @Input() categoricalFilterConfig: any;

  private phenoFiltersState: Observable<PhenoFiltersState>;
  private internalSelectedValue: string;

  constructor(
    private store: Store<any>
  ) {
    this.phenoFiltersState = this.store.select('phenoFilters');
  }

  ngOnInit() {
    this.store.dispatch({
      'type': PHENO_FILTERS_ADD_CATEGORICAL,
      'payload': {
        'name': this.categoricalFilterConfig.name,
        'role': this.categoricalFilterConfig.measureFilter.role,
        'measure': this.categoricalFilterConfig.measureFilter.measure
      }
    });

    this.phenoFiltersState.subscribe(
      (filtersState) => {
        for (let filter of filtersState.phenoFilters) {
          let categoricalFilter = filter as CategoricalFilterState;
          if (filter.id == this.categoricalFilterConfig.name) {
            if (!categoricalFilter.selection || categoricalFilter.selection.length == 0) {
              this.internalSelectedValue = null;
            }
            else {
              this.internalSelectedValue = categoricalFilter.selection[0];
            }
          }
        }
      }
    );
  }

  set selectedValue(value) {
    this.store.dispatch({
      'type': PHENO_FILTERS_CATEGORICAL_SET_SELECTION,
      'payload': {
        'id': this.categoricalFilterConfig.name,
        'selection': [value]
      }
    });
  }

  get selectedValue(): string {
    return this.internalSelectedValue;
  }

  clear() {
    this.store.dispatch({
      'type': PHENO_FILTERS_CATEGORICAL_SET_SELECTION,
      'payload': {
        'id': this.categoricalFilterConfig.name,
        'selection': []
      }
    });
  }

}
