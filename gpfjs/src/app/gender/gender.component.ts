import { Gender } from './gender';
import { Component, OnInit } from '@angular/core';
import { Select, Store } from '@ngxs/store';
import { Observable } from 'rxjs';
import { AddGender, GenderModel, GenderState, RemoveGender } from './gender.state';
import { validate } from 'class-validator';

@Component({
  selector: 'gpf-gender',
  templateUrl: './gender.component.html',
  styleUrls: ['./gender.component.css'],
})
export class GenderComponent implements OnInit {

  gender = new Gender();
  supportedGenders = ['male', 'female', 'unspecified'];
  errors: string[] = [];
  @Select(GenderState) state$: Observable<GenderModel>;

  constructor(private store: Store) { }

  ngOnInit() {
    this.selectAll();
    // this.store.selectOnce(state => state.genderState).subscribe(state => {
    //   for (const gender of state.genders) {
    //     this.genderCheckValue(gender, true);
    //   }
    // });

    this.state$.subscribe(() => {
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  selectAll() {
    for (const gender of this.supportedGenders) {
      this.gender[gender] = true;
      this.store.selectOnce(state => state.genderState).subscribe(state => {
        if (!state.genders.includes(gender)) {
          this.store.dispatch(new AddGender(gender));
        }
      });
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
