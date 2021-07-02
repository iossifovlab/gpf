import { Component, OnInit, OnChanges, Input, SimpleChanges } from '@angular/core';

import { Dataset } from '../datasets/datasets';
import { validate } from 'class-validator';
import { Store, Select } from '@ngxs/store';
import { Study } from '../study-filter/study-filter.component';
import { SetStudyFilters, StudyFiltersBlockState, StudyFiltersBlockModel } from './study-filters-block.state';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-study-filters-block',
  templateUrl: './study-filters-block.component.html',
  styleUrls: ['./study-filters-block.component.css'],
})
export class StudyFiltersBlockComponent implements OnInit, OnChanges {
  @Input() dataset: Dataset;

  studies: Study[] = [];
  selectedStudies: Study[] = [];

  @Select(StudyFiltersBlockState) state$: Observable<StudyFiltersBlockModel>;
  errors: Array<string> = [];

  constructor(private store: Store) { }

  ngOnChanges(changes: SimpleChanges) {
    let ids: string[] = changes.dataset.currentValue.studies;
    let names: string[] = changes.dataset.currentValue.studyNames;
    this.studies = [];
    for (let i = 0; i < ids.length; i++) {
        let study: Study = {
            "studyId": ids[i],
            "studyName": names[i]
        }
        this.studies.push(study)
    }
  }

  ngOnInit() {
    this.store.selectOnce(state => state.studyFiltersBlockState).subscribe(state => {
      // restore state
      for (const study of state.studyFilters) {
        for (const studyDesc of this.studies) {
          if (studyDesc.studyId === study.studyId) {
            this.addFilter(new Study(studyDesc.studyId, studyDesc.studyName));
          }
        }
      }
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  updateState() {
    this.store.dispatch(new SetStudyFilters(
      this.selectedStudies.map(st => st.studyId)
    ));
  }

  addFilter(studyFilter: Study = null) {
    if (studyFilter === null) {
      this.selectedStudies.push(new Study(
        this.studies[0].studyId,
        this.studies[0].studyName,
      ));
    } else {
      this.selectedStudies.push(studyFilter);
    }
    this.updateState();
  }

  removeFilter(studyFilter: Study) {
    this.selectedStudies = this.selectedStudies.filter(
      sf => sf.studyId !== studyFilter.studyId
    );
    this.updateState();
  }

  changeSelectedStudy(event: object) {
    const selectedStudy = event['selectedStudy'];
    const selectedStudyId = event['selectedStudyId'];
    for (const study of this.studies) {
      if (study.studyId === selectedStudyId) {
        selectedStudy.studyId = study.studyId;
        selectedStudy.studyName = study.studyName;
        break;
      }
    }
    this.updateState();
  }

  trackById(index: number, data: any) {
    return data.id;
  }
}
