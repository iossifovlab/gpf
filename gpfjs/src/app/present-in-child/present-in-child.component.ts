import {
  PresentInChildState, PRESENT_IN_CHILD_CHECK_ALL,
  PRESENT_IN_CHILD_UNCHECK_ALL, PRESENT_IN_CHILD_UNCHECK, PRESENT_IN_CHILD_CHECK
} from './present-in-child';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'
import { QueryData } from '../query/query'

@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PresentInChildComponent) }]
})
export class PresentInChildComponent implements OnInit {
  affectedOnly: boolean = true;
  unaffectedOnly: boolean = true;
  affectedUnaffected: boolean = true;
  neither: boolean = true;

  presentInChildState: Observable<PresentInChildState>;

  constructor(
    private store: Store<any>
  ) {

    this.presentInChildState = this.store.select('presentInChild');
  }

  ngOnInit() {
    this.presentInChildState.subscribe(
      state => {
        this.affectedOnly = state.indexOf('affected only') !== -1;
        this.unaffectedOnly = state.indexOf('unaffected only') !== -1;
        this.affectedUnaffected = state.indexOf('affected and unaffected') !== -1;
        this.neither = state.indexOf('neither') !== -1;
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
    (presentInChildState) => {
      // if (!isValid) {
      //   throw "invalid state"
      // }
      return { presentInChild: presentInChildState }
  });
}
}
