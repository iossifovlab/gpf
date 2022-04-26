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
  public presentInChildValues: Set<string> = new Set([
    'proband only', 'sibling only', 'proband and sibling', 'neither'
  ]);

  @Validate(SetNotEmpty, { message: 'Select at least one.' })
  public selectedValues = new Set<string>();

  public constructor(protected store: Store) {
    super(store, PresentInChildState, 'presentInChild');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.selectOnce(state => state.presentInChildState).subscribe(state => {
      // restore state
      this.updatePresentInChild(new Set([...state.presentInChild]));
    });
  }

  public updatePresentInChild(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(new SetPresentInChildValues(newValues));
  }
}
