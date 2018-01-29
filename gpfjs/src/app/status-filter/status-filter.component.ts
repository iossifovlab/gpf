import { Component, OnInit, forwardRef } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StatusFilter, ALL_STATES } from './status-filter';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-status-filter',
  templateUrl: './status-filter.component.html',
  styleUrls: ['./status-filter.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => StatusFilterComponent) }]
})
export class StatusFilterComponent extends QueryStateWithErrorsProvider implements OnInit {

  statusFilter = new StatusFilter();

  constructor(private stateRestoreService: StateRestoreService) {
  	super();
  }

  ngOnInit() {
  	this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['status']) {
          this.statusFilter.selected = new Set(state['status'] as string[]);
        }
      });
  }

  selectAll(): void {
    this.statusFilter.selected = new Set(ALL_STATES);
  }

  selectNone(): void {
    this.statusFilter.selected = new Set();
  }

  statusFilterCheckValue(key: string, value: boolean): void {
    if (value) {
      this.statusFilter.selected.add(key);
    } else {
      this.statusFilter.selected.delete(key);
    }
  }

  getState() {
    return this.validateAndGetState(this.statusFilter)
      .map(statusFilter => {
      	return {
      		status: Array.from(statusFilter.selected)
      	};
	});
  }

}
