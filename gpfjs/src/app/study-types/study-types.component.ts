import { Component, OnInit } from '@angular/core';
import { Store } from '@ngxs/store';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { SetStudyTypes, StudyTypesState } from './study-types.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-study-types',
  templateUrl: './study-types.component.html',
})
export class StudyTypesComponent extends StatefulComponent implements OnInit {
  public studyTypes: Set<string> = new Set(['we', 'wg', 'tg']);
  public studyTypesDisplayNames: Map<string, string>;

  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedValues: Set<string> = new Set<string>([]);

  public constructor(protected store: Store) {
    super(store, StudyTypesState, 'studyTypes');
    this.studyTypesDisplayNames = new Map();
    this.studyTypesDisplayNames.set('we', 'Whole exome');
    this.studyTypesDisplayNames.set('tg', 'Targeted genome');
    this.studyTypesDisplayNames.set('wg', 'Whole genome');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.selectOnce(state => state.studyTypesState).subscribe(state => {
      // restore state
      if (state.studyTypes.length) {
        this.selectedValues = new Set(state.studyTypes);
      }
    });
  }

  public updateStudyTypes(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(new SetStudyTypes(newValues));
  }
}
