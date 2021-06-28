import { Component, OnInit } from '@angular/core';
import { IsNotEmpty } from 'class-validator';
import { validate } from 'class-validator';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { SetPersonIds, PersonIdsModel, PersonIdsState } from './person-ids.state';

export class PersonIds {
  @IsNotEmpty()
  personIds = '';
}

@Component({
  selector: 'gpf-person-ids',
  templateUrl: './person-ids.component.html',
  styleUrls: ['./person-ids.component.css'],
})
export class PersonIdsComponent implements OnInit {

  personIds = new PersonIds();
  errors: Array<string> = [];

  @Select(PersonIdsState) state$: Observable<PersonIdsModel>;

  constructor(
    private store: Store
  ) { }

  ngOnInit() {
    this.store.selectOnce(state => state.personIdsState).subscribe(state => {
      // restore state
      this.personIds.personIds = state.personIds.join('\n');
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this.personIds).then(errors => { this.errors = errors.map(err => String(err)); });
    });
  }

  setPersonIds(personIds: string) {
    const result = personIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.personIds.personIds = personIds;
    this.store.dispatch(new SetPersonIds(result));
  }

}
