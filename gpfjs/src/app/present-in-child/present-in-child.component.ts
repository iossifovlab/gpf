import { Component, OnInit, forwardRef } from '@angular/core';
import { validate } from 'class-validator';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';

import { PresentInChild, ALL_STATES } from './present-in-child';
import { AddPresentInChildValue, RemovePresentInChildValue, PresentInChildModel, PresentInChildState } from './present-in-child.state';

// TODO: rewrite template
@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
})
export class PresentInChildComponent implements OnInit {

  presentInChild = new PresentInChild();
  @Select(PresentInChildState) state$: Observable<PresentInChildModel>;
  errors: Array<string> = [];

  constructor(
    private store: Store
  ) { }

  ngOnInit() {
    this.store.selectOnce(state => state.presentInChildState).subscribe(state => {
      // restore state
      this.presentInChild.selected.clear();
      for (const inh of state.presentInChild) {
        this.addPresentInChildValue(inh);
      }
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this.presentInChild).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  addPresentInChildValue(presentInChild: string) {
    this.presentInChild.selected.add(presentInChild);
    this.store.dispatch(new AddPresentInChildValue(presentInChild));
  }

  removePresentInChildValue(presentInChild: string) {
    this.presentInChild.selected.delete(presentInChild);
    this.store.dispatch(new RemovePresentInChildValue(presentInChild));
  }

  presentInChildCheckValue(key: string, value: boolean): void {
    if (value) {
      this.addPresentInChildValue(key);
    } else {
      this.removePresentInChildValue(key);
    }
  }

  selectAll() {
    for (const pic of ALL_STATES) {
      this.addPresentInChildValue(pic);
    }
  }

  selectNone() {
    for (const inh of ALL_STATES) {
      this.removePresentInChildValue(inh);
    }
  }
}
