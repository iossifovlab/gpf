import { Component, OnInit, OnChanges, Input, forwardRef, SimpleChanges } from '@angular/core';

import { Dataset } from '../datasets/datasets';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

import { StudyFiltersState, StudyFilterState } from '../study-filter/study-filter-store';

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
  studies: string[];

  addFilter(studyFilterState: StudyFilterState = null) {
    if (!studyFilterState) {
        studyFilterState = new StudyFilterState();
        studyFilterState.studyName = this.studies[0];
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
  ){
    super();
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name)
        .take(1)
        .subscribe(state => {
          if (state['studyFilters'] && state['studyFilters'].length > 0) {
            for (let studyName of state['studyFilters']) {
              let studyFilter = new StudyFilterState();
              studyFilter.studyName = studyName.studyName;
              this.addFilter(studyFilter);
            }
          }
        });
  }

  ngOnInit() {
    this.restoreStateSubscribe();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.studies = changes.dataset.currentValue.studies.split(',');
  }

  getState() {
    return this.validateAndGetState(this.studyFiltersState)
               .map(studyFiltersState => {
                   return {
                     studyFilters: studyFiltersState.studyFiltersState
                       .map(el => {
                         return {
                           studyName: el.studyName
                         };
                       })
                   };
               });
    }

}
