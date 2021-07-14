import { Component, OnInit } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngxs/store';
import { SetPresentInChildValues, PresentInChildState } from './present-in-child.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
})
export class PresentInChildComponent extends StatefulComponent implements OnInit {

  presentInChildValues: Set<string> = new Set([
    'proband only', 'sibling only', 'proband and sibling', 'neither'
  ]);

  @Validate(SetNotEmpty, { message: 'select at least one' })
  selectedValues = new Set();

  constructor(protected store: Store) {
    super(store, PresentInChildState, 'presentInChild');
  }

  ngOnInit() {
    super.ngOnInit();
    this.store.selectOnce(state => state.presentInChildState).subscribe(state => {
      // restore state
      this.selectedValues = new Set([...state.presentInChild]);
    });
  }

  updatePresentInChild(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(new SetPresentInChildValues(newValues));
  }
}
