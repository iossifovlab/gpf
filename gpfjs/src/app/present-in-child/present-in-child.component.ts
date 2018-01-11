import { PresentInChild, ALL_STATES } from './present-in-child';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { QueryData } from '../query/query';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { StateRestoreService } from '../store/state-restore.service';

// TODO: rewrite template
@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
  providers: [{
    provide: QueryStateProvider, useExisting: forwardRef(() => PresentInChildComponent) }]
})
export class PresentInChildComponent extends QueryStateWithErrorsProvider implements OnInit {

  presentInChild = new PresentInChild();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['presentInChild']) {
          this.presentInChild.selected = new Set(state['presentInChild'] as string[]);
        }
      });

  }

  selectAll(): void {
    this.presentInChild.selected = new Set(ALL_STATES);
  }

  selectNone(): void {
    this.presentInChild.selected = new Set();
  }

  presentInChildCheckValue(key: string, value: boolean): void {
    if (value) {
      this.presentInChild.selected.add(key);
    } else {
      this.presentInChild.selected.delete(key);
    }
  }

  getState() {
    return this.validateAndGetState(this.presentInChild)
      .map(state => {
        return {
          presentInChild: Array.from(state.selected)
        };
      });
  }
}
