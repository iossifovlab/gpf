import { Component, OnInit, OnChanges, Input, SimpleChanges } from '@angular/core';
import { Store } from '@ngxs/store';
import { Dataset } from '../datasets/datasets';
import { Study } from '../study-filter/study-filter.component';
import { SetStudyFilters, StudyFiltersBlockState } from './study-filters-block.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { ValidateNested } from 'class-validator';

@Component({
  selector: 'gpf-study-filters-block',
  templateUrl: './study-filters-block.component.html',
  styleUrls: ['./study-filters-block.component.css'],
})
export class StudyFiltersBlockComponent extends StatefulComponent implements OnInit, OnChanges {
  @Input() dataset: Dataset;

  @ValidateNested({each: true})
  studies: Study[] = [];

  @ValidateNested({each: true})
  selectedStudies: Study[] = [];

  constructor(protected store: Store) {
    super(store, StudyFiltersBlockState, 'studyFiltersBlock');
  }

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
    super.ngOnInit();
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
