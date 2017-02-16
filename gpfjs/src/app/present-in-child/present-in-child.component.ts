import {
  PresentInChildState, PRESENT_IN_CHILD_CHECK_ALL,
  PRESENT_IN_CHILD_UNCHECK_ALL, PRESENT_IN_CHILD_UNCHECK, PRESENT_IN_CHILD_CHECK
} from './present-in-child';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
})
export class PresentInChildComponent implements OnInit {
  autismOnly: boolean = true;
  unaffectedOnly: boolean = true;
  autismUnaffected: boolean = true;
  neither: boolean = true;

  presentInChildState: Observable<PresentInChildState>;

  constructor(
    private store: Store<any>
  ) {

    this.presentInChildState = this.store.select('presentInChild');
  }

  ngOnInit() {
    this.presentInChildState.subscribe(
      genderState => {
        this.autismOnly = genderState.autismOnly;
        this.unaffectedOnly = genderState.unaffectedOnly;
        this.autismUnaffected = genderState.autismUnaffected;
        this.neither = genderState.neither;
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
    if (key === 'autismOnly' || key === 'unaffectedOnly' || key === 'autismUnaffected' || key === 'neither') {
      this.store.dispatch({
        'type': value ? PRESENT_IN_CHILD_CHECK : PRESENT_IN_CHILD_UNCHECK,
        'payload': key
      });
    }
  }
}
