import { Component, OnInit } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngrx/store';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';
import { selectPresentInChild, setPresentInChild } from './present-in-child.state';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
})
export class PresentInChildComponent extends StatefulComponentNgRx implements OnInit {
  public presentInChildValues: Set<string> = new Set([
    'proband only', 'sibling only', 'proband and sibling', 'neither'
  ]);

  @Validate(SetNotEmpty, { message: 'Select at least one.' })
  public selectedValues = new Set<string>();

  public constructor(protected store: Store) {
    super(store, 'presentInChild', selectPresentInChild);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.select(selectPresentInChild).pipe(take(1)).subscribe(presentInChildState => {
      // restore state
      this.updatePresentInChild(new Set([...presentInChildState]));
    });
  }

  public updatePresentInChild(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(setPresentInChild({presentInChild: [...newValues]}));
  }
}
