import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { selectStudyTypes, setStudyTypes } from './study-types.state';
import { ComponentValidator } from 'app/common/component-validator';
import { take } from 'rxjs';

@Component({
    selector: 'gpf-study-types',
    templateUrl: './study-types.component.html',
    standalone: false
})
export class StudyTypesComponent extends ComponentValidator implements OnInit {
  public studyTypes: Set<string> = new Set(['we', 'wg', 'tg']);
  public studyTypesDisplayNames: Map<string, string>;

  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedValues: Set<string> = new Set<string>([]);

  public constructor(protected store: Store) {
    super(store, 'studyTypes', selectStudyTypes);
    this.studyTypesDisplayNames = new Map();
    this.studyTypesDisplayNames.set('we', 'Whole exome');
    this.studyTypesDisplayNames.set('tg', 'Targeted genome');
    this.studyTypesDisplayNames.set('wg', 'Whole genome');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.select(selectStudyTypes).pipe(take(1)).subscribe(studyTypesState => {
      if (studyTypesState.length) {
        this.selectedValues = new Set(studyTypesState);
      }
    });
  }

  public updateStudyTypes(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(setStudyTypes({studyTypes: [...newValues]}));
  }
}
