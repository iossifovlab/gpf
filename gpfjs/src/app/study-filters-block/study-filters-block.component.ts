import { Component, OnInit, OnChanges, Input, forwardRef, SimpleChanges } from '@angular/core';

import { Dataset } from '../datasets/datasets';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

import { StudyFiltersState, StudyFilterState, StudyDescriptor } from '../study-filter/study-filter-store';

@Component({
  selector: 'gpf-study-filters-block',
  templateUrl: './study-filters-block.component.html',
  styleUrls: ['./study-filters-block.component.css'],
  providers: [{
        provide: QueryStateProvider,
        useExisting: forwardRef(() => StudyFiltersBlockComponent)
    }]
})
export class StudyFiltersBlockComponent extends QueryStateWithErrorsProvider implements OnInit, OnChanges {
  @Input() dataset: Dataset;
  studyFiltersState = new StudyFiltersState();
  studies: StudyDescriptor[];

  addFilter(studyFilterState: StudyFilterState = null) {
    if (!studyFilterState) {
        studyFilterState = new StudyFilterState();
        studyFilterState.study = this.studies[0];
    }
    this.studyFiltersState.studyFiltersState.push(studyFilterState);
  }

  removeFilter(studyFilter: StudyFilterState) {
     this.studyFiltersState.studyFiltersState = this.studyFiltersState
         .studyFiltersState.filter(sf => sf !== studyFilter);
  }

  trackById(index: number, data: any) {
    return data.id;
  }

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name)
        .take(1)
        .subscribe(state => {
          if (state['studyFilters'] && state['studyFilters'].length > 0) {
            for (let study of state['studyFilters']) {
              let studyFilter = new StudyFilterState();
              for(let studyDesc of this.studies) {
                  if(studyDesc.studyId === study.studyId) {
                      studyFilter.study = studyDesc;
                  }
              }
              this.addFilter(studyFilter);
            }
          }
        });
  }

  ngOnInit() {
    this.restoreStateSubscribe();
  }

  ngOnChanges(changes: SimpleChanges) {
    let ids: string[] = changes.dataset.currentValue.studies;
    let names: string[] = changes.dataset.currentValue.studyNames;
    this.studies = [];
    for(let i = 0; i < ids.length; i++) {
        let study: StudyDescriptor = {
            "studyId": ids[i],
            "studyName": names[i]
        }
        this.studies.push(study)
    }
  }

  getState() {
    return this.validateAndGetState(this.studyFiltersState)
               .map(studyFiltersState => {
                   return {
                     studyFilters: studyFiltersState.studyFiltersState
                       .map(el => {
                         return {
                           studyId: el.study.studyId
                         };
                       })
                   };
               });
    }

}
