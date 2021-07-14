import { Gender } from './gender';
import { Component, OnInit } from '@angular/core';
import { Store } from '@ngxs/store';
import { AddGender, GenderState, RemoveGender } from './gender.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { ValidateNested } from 'class-validator';

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css'],
})
export class GenderComponent extends StatefulComponent implements OnInit {

  @ValidateNested()
  gender = new Gender();
  supportedGenders = ['male', 'female', 'unspecified'];

  constructor(protected store: Store) {
    super(store, GenderState, 'gender');
  }

  ngOnInit() {
    super.ngOnInit();
    this.store.selectOnce(state => state.genderState).subscribe(state => {
      if (state.genders) {
        this.selectNone();
        for (const gender of state.genders) {
          this.genderCheckValue(gender, true);
        }
      }
    });
  }

  selectAll() {
    for (const gender of this.supportedGenders) {
      this.gender[gender] = true;
      this.store.dispatch(new AddGender(gender));
    }
  }

  selectNone() {
    for (const gender of this.supportedGenders) {
      this.gender[gender] = false;
      this.store.dispatch(new RemoveGender(gender));
    }
  }

  genderCheckValue(gender: string, value: boolean): void {
    this.gender[gender] = value;

    if (value) {
      this.store.dispatch(new AddGender(gender));
    } else {
      this.store.dispatch(new RemoveGender(gender));
    }
  }
}
