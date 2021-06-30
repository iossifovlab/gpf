import { Component, OnInit, forwardRef } from '@angular/core';
import { Validate, validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { SetPresentInChildValues, PresentInChildModel, PresentInChildState } from './present-in-child.state';

@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
})
export class PresentInChildComponent implements OnInit {

  presentInChildValues: Set<string> = new Set([
    'proband only', 'sibling only', 'proband and sibling', 'neither'
  ]);

  @Validate(SetNotEmpty, { message: 'select at least one' })
  selectedValues = new Set();

  @Select(PresentInChildState) state$: Observable<PresentInChildModel>;
  errors: Array<string> = [];

  constructor(
    private store: Store
  ) { }

  ngOnInit() {
    this.store.selectOnce(state => state.presentInChildState).subscribe(state => {
      // restore state
      this.selectedValues = new Set([...state.presentInChild]);
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  updatePresentInChild(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(new SetPresentInChildValues(newValues));
  }
}
