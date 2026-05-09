import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectInheritanceTypes, setInheritanceTypes } from './inheritancetypes.state';
import { take } from 'rxjs';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-inheritancetypes',
  templateUrl: './inheritancetypes.component.html',
  standalone: false
})
export class InheritancetypesComponent implements OnInit {
  @Input() public inheritanceTypes: Set<string>;
  @Input() public selectedValues: Set<string> = new Set();
  public inheritanceTypeDisplayNames: Map<string, string>;
  public errors: string[] = [];

  public constructor(protected store: Store) {
    this.inheritanceTypeDisplayNames = new Map();
    this.inheritanceTypeDisplayNames.set('reference', 'Reference');
    this.inheritanceTypeDisplayNames.set('mendelian', 'Mendelian');
    this.inheritanceTypeDisplayNames.set('denovo', 'Denovo');
    this.inheritanceTypeDisplayNames.set('possible_denovo', 'Possible denovo');
    this.inheritanceTypeDisplayNames.set('omission', 'Omission');
    this.inheritanceTypeDisplayNames.set('possible_omission', 'Possible omission');
    this.inheritanceTypeDisplayNames.set('other', 'Other');
    this.inheritanceTypeDisplayNames.set('missing', 'Missing');
    this.inheritanceTypeDisplayNames.set('unknown', 'Unknown');
  }

  public ngOnInit(): void {
    this.store.select(selectInheritanceTypes).pipe(take(1)).subscribe(inheritanceTypesState => {
      this.selectedValues = new Set(inheritanceTypesState);
      this.validateState();
    });
  }

  public updateInheritanceTypes(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.validateState();
    this.store.dispatch(setInheritanceTypes({inheritanceTypes: [...newValues]}));
  }

  private validateState(): void {
    this.errors = [];
    if (!this.selectedValues.size) {
      this.errors.push('Select at least one.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'inheritanceTypes', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'inheritanceTypes'}));
    }
  }
}
