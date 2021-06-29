import { Input, Component, OnInit, forwardRef } from '@angular/core';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { validate, Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { SetStudyTypes, StudyTypesModel, StudyTypesState } from './study-types.state';

@Component({
  selector: 'gpf-study-types',
  templateUrl: './study-types.component.html',
})
export class StudyTypesComponent implements OnInit {

  /*
   * we: Whole Exome
   * tg: Targeted Genome
   * wg: Whole Genome
   */
  studyTypes: Set<string> = new Set(['we', 'tg', 'wg']);

  @Input()
  @Validate(SetNotEmpty, {message: 'select at least one'})
  selectedValues: Set<string> = new Set([]);

  @Select(StudyTypesState) state$: Observable<StudyTypesModel>;
  errors: Array<string> = [];

  constructor(private store: Store) { }

  ngOnInit() {
    this.store.selectOnce(state => state.studyTypesState).subscribe(state => {
      // restore state
      this.selectedValues = state.studyTypes;
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  updateStudyTypes(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(new SetStudyTypes(newValues));
  }
}
