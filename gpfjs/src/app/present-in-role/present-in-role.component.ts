import { Component, OnInit, Input, forwardRef } from '@angular/core';

import { PresentInRoleSelector } from './present-in-role';

import { QueryStateWithErrorsProvider, QueryStateProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { PresentInRole } from 'app/datasets/datasets';

@Component({
  selector: 'gpf-present-in-role',
  templateUrl: './present-in-role.component.html',
  styleUrls: ['./present-in-role.component.css'],
  providers: [{
    provide: QueryStateProvider, useExisting: forwardRef(() => PresentInRoleComponent) }]
})
export class PresentInRoleComponent extends QueryStateWithErrorsProvider implements OnInit {
  @Input() presentInRole: PresentInRole;

  presentInRoleSelector = new PresentInRoleSelector();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['presentInRole'] && state['presentInRole'][this.presentInRole.id]) {
          this.presentInRoleSelector.selected =
            new Set(state['presentInRole'][this.presentInRole.id] as string[]);
        }
      });

  }

  selectAll(): void {
    this.presentInRoleSelector.selected = new Set(this.presentInRole.roles);
    this.presentInRoleSelector.selected.add('neither');
  }

  selectNone(): void {
    this.presentInRoleSelector.selected = new Set();
  }

  presentInRoleCheckValue(key: string, value: boolean): void {
    if (value) {
      this.presentInRoleSelector.selected.add(key);
    } else {
      this.presentInRoleSelector.selected.delete(key);
    }
  }

  getState() {
    return this.validateAndGetState(this.presentInRoleSelector)
      .map(state => {
        return {
          presentInRole: {
            [this.presentInRole.id]: Array.from(state.selected)
          }
        };
      });
  }

}
