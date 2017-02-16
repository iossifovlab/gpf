import {
  RegionsFilterState, REGIONS_FILTER_CHANGE
} from './regions-filter';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
})
export class RegionsFilterComponent implements OnInit {
  regionsFilterInternal: string;

  regionsFilterState: Observable<RegionsFilterState>;

  constructor(
    private store: Store<any>
  ) {

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

}
