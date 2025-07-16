import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { addGender, removeGender, selectGenders } from './gender.state';
import { take } from 'rxjs';
import { setErrors, resetErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css'],
  standalone: false
})
export class GenderComponent implements OnInit {
  public selectedGenders: string[] = [];
  public supportedGenders = ['male', 'female', 'unspecified'];
  @Input() public hasZygosity: boolean;
  public errors: string[] = [];

  public constructor(protected store: Store) {}

  public ngOnInit(): void {
    this.store.select(selectGenders).pipe(take(1)).subscribe(gendersState => {
      for (const gender of gendersState) {
        this.selectedGenders.push(gender);
      }
      this.validateState();
    });
  }

  public isChecked(gender: string): boolean {
    return this.selectedGenders.includes(gender);
  }

  public selectAll(): void {
    for (const gender of this.supportedGenders) {
      this.selectedGenders.push(gender);
      this.store.dispatch(addGender({gender: gender}));
    }
    this.validateState();
  }

  public selectNone(): void {
    this.selectedGenders = [];
    this.validateState();
    for (const gender of this.supportedGenders) {
      this.store.dispatch(removeGender({gender: gender}));
    }
  }

  public genderCheckValue(gender: string, isChecked: boolean): void {
    if (isChecked) {
      this.selectedGenders.push(gender);
      this.store.dispatch(addGender({gender: gender}));
    } else {
      const index = this.selectedGenders.indexOf(gender);
      this.selectedGenders.splice(index, 1);
      this.store.dispatch(removeGender({gender: gender}));
    }
    this.validateState();
  }

  private validateState(): void {
    this.errors = [];
    if (!this.selectedGenders.length) {
      this.errors.push('Select at least one.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'genders', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'genders'}));
    }
  }
}
