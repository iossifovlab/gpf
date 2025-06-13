import { Component, Input, OnInit } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngrx/store';
import { selectInheritanceTypes, setInheritanceTypes } from './inheritancetypes.state';
import { ComponentValidator } from 'app/common/component-validator';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-inheritancetypes',
  templateUrl: './inheritancetypes.component.html'
})
export class InheritancetypesComponent extends ComponentValidator implements OnInit {
  @Input()
  public inheritanceTypes: Set<string>;
  public inheritanceTypeDisplayNames: Map<string, string>;

  @Input()
  @Validate(SetNotEmpty, { message: 'Select at least one.' })
  public selectedValues: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, 'inheritanceTypes', selectInheritanceTypes);
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
    });
  }

  public updateInheritanceTypes(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(setInheritanceTypes({inheritanceTypes: [...newValues]}));
  }
}
