import {
  RegionsFilterState, REGIONS_FILTER_CHANGE, REGIONS_FILTER_INIT
} from './regions-filter';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => RegionsFilterComponent) }]
})
export class RegionsFilterComponent extends QueryStateProvider implements OnInit {
  regionsFilterInternal: string;

  regionsFilterState: Observable<[RegionsFilterState, boolean, ValidationError[]]>;
  flashingAlert = false;
  errors: string[];

  constructor(
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  ) {
    super();
    this.regionsFilterState = toObservableWithValidation(RegionsFilterState ,this.store.select('regionsFilter'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': REGIONS_FILTER_INIT,
    });

    this.stateRestoreService.getState(this.constructor.name).subscribe(
      (state) => {
        if (state['regions']) {
          this.store.dispatch({
            'type': REGIONS_FILTER_CHANGE,
            'payload': state['regions'].join("\n")
          });
        }
      }
    )

    this.regionsFilterState.subscribe(
      ([regionsFilterState, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);
        this.regionsFilterInternal = regionsFilterState.regionsFilter;
      }
    );
  }

  set regionsFilter(regionsFilter: string) {
    this.store.dispatch({
      'type': REGIONS_FILTER_CHANGE,
      'payload': regionsFilter
    });
  }

  get regionsFilter() {
    return this.regionsFilterInternal;
  }

  getState() {
    return this.regionsFilterState.take(1).map(
      ([regionsFilterState, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)
          throw "invalid state"
        }

        let regionsFilter: string = regionsFilterState.regionsFilter;
        let result = regionsFilter
          .split(/[\s]/)
          .map(s => s.replace(/[,]/g, ''))
          .filter(s => s !== '');
        if (result.length === 0) {
          return {};
        }

        return { regions: result }
    });
  }

}
