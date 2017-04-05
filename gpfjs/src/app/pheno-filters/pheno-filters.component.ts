import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { PhenoFilter } from '../datasets/datasets';
import { QueryStateProvider } from '../query/query-state-provider'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { Store } from '@ngrx/store';
import {
  PhenoFilterState, PhenoFiltersState, CategoricalFilterState,
  ContinuousFilterState,  PHENO_FILTERS_INIT
} from './pheno-filters';
import { Observable } from 'rxjs/Observable';
import { ValidationError } from "class-validator";
import { validate } from "class-validator";
import { plainToClass } from "class-transformer";

@Component({
  selector: 'gpf-pheno-filters',
  templateUrl: './pheno-filters.component.html',
  styleUrls: ['./pheno-filters.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PhenoFiltersComponent) }]
})
export class PhenoFiltersComponent extends QueryStateProvider implements OnInit {
  @Input() phenoFilters: Array<PhenoFilter>;
  @Input() datasetId: string;

  private phenoFiltersState: Observable<[Array<PhenoFilterState>, boolean, ValidationError[]]>;

  constructor(
    private store: Store<any>
  ) {
    super();

    this.phenoFiltersState = this.store.select("phenoFilters").switchMap(
      (phenoFiltersState: PhenoFiltersState) => {
        let filters = phenoFiltersState.phenoFilters.map(
          (value) => {
            if (value.measureType == "categorical") {
              return plainToClass(CategoricalFilterState, value)
            }
            else {
              return plainToClass(ContinuousFilterState, value)
            }
        })

        return Observable.fromPromise(validate(filters)).map(validationState => {
          return [filters, true, []];
        })
        .catch(errors => {
          return Observable.of([filters, false, errors]);
        });

      }
    );
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

  getState() {
    return this.phenoFiltersState.take(1).map(
      ([phenoFiltersState, isValid, validationErrors]) => {
        if (!isValid) {
          //this.flashingAlert = true;
          //setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid state"
        }
        let phenoFilters = phenoFiltersState.filter(
          (filter) => {
            return !filter.isEmpty();
          }
        );

        return { phenoFilters: phenoFilters }
    });
  }

}
