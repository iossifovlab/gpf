import {
  RegionsFilterState, REGIONS_FILTER_CHANGE
} from './regions-filter';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => RegionsFilterComponent) }]
})
export class RegionsFilterComponent extends QueryStateProvider implements OnInit {
  regionsFilterInternal: string;

  regionsFilterState: Observable<RegionsFilterState>;

  constructor(
    private store: Store<any>
  ) {
    super();
    this.regionsFilterState = this.store.select('regionsFilter');
  }

  ngOnInit() {
    this.regionsFilterState.subscribe(
      regionsFilterState => {
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
      (regionsFilterState) => {
        let regionsFilter: string = regionsFilterState.regionsFilter;
        let result = regionsFilter
          .split(/[\s]/)
          .map(s => s.replace(/[,]/g, ''))
          .filter(s => s !== '');
        if (result.length === 0) {
          return {};
        }
        // if (!isValid) {
        //   throw "invalid state"
        // }
        return { regions: result }
    });
  }

}
