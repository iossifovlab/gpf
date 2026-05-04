import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectPresentInChild, setPresentInChild } from './present-in-child.state';
import { take } from 'rxjs';
import { setErrors, resetErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-present-in-child',
  templateUrl: './present-in-child.component.html',
  styleUrls: ['./present-in-child.css'],
  standalone: false
})
export class PresentInChildComponent implements OnInit {
  @Input() public hasZygosity: boolean;
  public presentInChildValues: Set<string> = new Set([
    'proband only', 'sibling only', 'proband and sibling', 'neither'
  ]);

  public selectedValues = new Set<string>();
  public errors: string[] = [];

  public constructor(protected store: Store) {}

  public ngOnInit(): void {
    this.store.select(selectPresentInChild).pipe(take(1)).subscribe(presentInChildState => {
      // restore state
      this.selectedValues = new Set(presentInChildState);
      this.validateState();
    });
  }

  public updatePresentInChild(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.validateState();
    this.store.dispatch(setPresentInChild({presentInChild: [...newValues]}));
  }

  private validateState(): void {
    this.errors = [];
    if (!this.selectedValues.size) {
      this.errors.push('Select at least one.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'presentInChild', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'presentInChild'}));
    }
  }
}
