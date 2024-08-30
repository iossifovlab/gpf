import { Gender } from './gender';
import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';
import { ValidateNested } from 'class-validator';
import { addGender, removeGender, selectGenders } from './gender.state';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css'],
})
export class GenderComponent extends StatefulComponentNgRx implements OnInit {
  @ValidateNested()
  public gender = new Gender();
  public supportedGenders = ['male', 'female', 'unspecified'];

  public constructor(protected store: Store) {
    super(store, 'genders', selectGenders);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.select(selectGenders).pipe(take(1)).subscribe(gendersState => {
      if (gendersState) {
        this.selectNone();
        for (const gender of gendersState) {
          this.genderCheckValue(gender, true);
        }
      }
    });
  }

  public selectAll(): void {
    for (const gender of this.supportedGenders) {
      this.gender[gender] = true;
      this.store.dispatch(addGender({gender: gender}));
    }
  }

  public selectNone(): void {
    for (const gender of this.supportedGenders) {
      this.gender[gender] = false;
      this.store.dispatch(removeGender({gender: gender}));
    }
  }

  public genderCheckValue(gender: string, value: boolean): void {
    this.gender[gender] = value;

    if (value) {
      this.store.dispatch(addGender({gender: gender}));
    } else {
      this.store.dispatch(addGender({gender: gender}));
    }
  }
}
