import { Component, OnInit, forwardRef, Input } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { RolesFilter } from './roles-filter';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-roles-filter',
  templateUrl: './roles-filter.component.html',
  styleUrls: ['./roles-filter.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => RolesFilterComponent) }]
})
export class RolesFilterComponent extends QueryStateWithErrorsProvider implements OnInit {

  rolesFilter = new RolesFilter();

  @Input()
  availableRoles: Array<string>;

  constructor(private stateRestoreService: StateRestoreService) {
  	super();
  }

  ngOnInit() {
  	this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['roles']) {
          this.rolesFilter.selected = new Set(state['roles'] as string[]);
        }
      });
  }

  selectAll(): void {
    this.rolesFilter.selected = new Set(this.availableRoles);
  }

  selectNone(): void {
    this.rolesFilter.selected = new Set();
  }

  rolesFilterCheckValue(key: string, value: boolean): void {
  	console.log(value)
    if (value) {
      this.rolesFilter.selected.add(key);
    } else {
      this.rolesFilter.selected.delete(key);
    }
  }

  getState() {
    return this.validateAndGetState(this.rolesFilter)
      .map(rolesFilter => {
      	return {
      		roles: Array.from(rolesFilter.selected)
      	};
	});
  }

}
