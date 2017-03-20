import {
  PresentInChildState, PRESENT_IN_CHILD_CHECK_ALL, PRESENT_IN_CHILD_INIT,
  PRESENT_IN_CHILD_UNCHECK_ALL, PRESENT_IN_CHILD_UNCHECK, PRESENT_IN_CHILD_CHECK
} from './present-in-child';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'
import { QueryData } from '../query/query'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PresentInChildComponent) }]
})
export class PresentInChildComponent extends QueryStateProvider implements OnInit {
  affectedOnly: boolean = true;
  unaffectedOnly: boolean = true;
  affectedUnaffected: boolean = true;
  neither: boolean = true;

  presentInChildState: Observable<[PresentInChildState, boolean, ValidationError[]]>;

  private errors: string[];
  private flashingAlert = false;

  constructor(
    private store: Store<any>
  ) {
    super();
    this.presentInChildState = toObservableWithValidation(PresentInChildState, this.store.select('presentInChild'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': PRESENT_IN_CHILD_INIT,
    });

    this.presentInChildState.subscribe(
      ([state, isValid, validationErrors]) => {
        console.log("presentInChildState", state)

        this.errors = validationErrorsToStringArray(validationErrors);

        this.affectedOnly = state.selected.indexOf('affected only') !== -1;
        this.unaffectedOnly = state.selected.indexOf('unaffected only') !== -1;
        this.affectedUnaffected = state.selected.indexOf('affected and unaffected') !== -1;
        this.neither = state.selected.indexOf('neither') !== -1;
      }
    );
  }

  selectAll(): void {
    this.store.dispatch({
      'type': PRESENT_IN_CHILD_CHECK_ALL,
    });
  }

  selectNone(): void {
    this.store.dispatch({
      'type': PRESENT_IN_CHILD_UNCHECK_ALL,
    });
  }

  presentInChildCheckValue(key: string, value: boolean): void {
    this.store.dispatch({
      'type': value ? PRESENT_IN_CHILD_CHECK : PRESENT_IN_CHILD_UNCHECK,
      'payload': key
    });
  }

  getState() {
    return this.presentInChildState.take(1).map(
      ([state, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

           throw "invalid state"
        }
        return { presentInChild: state.selected }
    });
  }
}
