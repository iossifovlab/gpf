import { RegionsFilter } from './regions-filter';
import { Component, OnInit, forwardRef } from '@angular/core';

import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-regions-filter',
  templateUrl: './regions-filter.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => RegionsFilterComponent) }]
})
export class RegionsFilterComponent extends QueryStateWithErrorsProvider implements OnInit {

  regionsFilter = new RegionsFilter();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['regions']) {
          this.regionsFilter.regionsFilter = state['regions'].join('\n');
        }
      });
  }


  getState() {
    return this.validateAndGetState(this.regionsFilter)
      .map(state => {
        const regionsFilter: string = state.regionsFilter;
        const result = regionsFilter
          .split(/[\s]/)
          .map(s => s.replace(/[,]/g, ''))
          .filter(s => s !== '');
        if (result.length === 0) {
          return {};
        }

        return { regions: result };
      });
  }

}
