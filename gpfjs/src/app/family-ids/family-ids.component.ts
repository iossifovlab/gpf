import { Component, OnInit } from '@angular/core';
import { FamilyIds } from './family-ids';
import { validate } from 'class-validator';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { SetFamilyIds, FamilyIdsModel, FamilyIdsState} from './family-ids.state';

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html',
  styleUrls: ['./family-ids.component.css'],
})
export class FamilyIdsComponent implements OnInit {

  familyIds = new FamilyIds();
  errors: Array<string> = [];

  @Select(FamilyIdsState) state$: Observable<FamilyIdsModel>;

  constructor(
    private store: Store
  ) { }

  ngOnInit() {
    this.store.selectOnce(state => state.familyIdsState).subscribe(state => {
      // restore state
      this.familyIds.familyIds = state.familyIds.join('\n');
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this.familyIds).then(errors => { this.errors = errors.map(err => String(err)); });
    });
  }

  setFamilyIds(familyIds: string) {
    const result = familyIds
      .split(/[,\s]/)
      .filter(s => s !== '');
    this.familyIds.familyIds = familyIds;
    this.store.dispatch(new SetFamilyIds(result));
  }
}
