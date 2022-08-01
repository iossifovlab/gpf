import { Component, OnInit, Input, ViewChild } from '@angular/core';
import { Store } from '@ngxs/store';
import { Dataset } from '../datasets/datasets';
import { SetStudyFilters, StudyFiltersBlockModel, StudyFiltersBlockState } from './study-filters-block.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { StateReset } from 'ngxs-reset-plugin';
import { SetNotEmpty } from 'app/utils/set.validators';
import { Validate } from 'class-validator';

@Component({
  selector: 'gpf-study-filters-block',
  templateUrl: './study-filters-block.component.html',
  styleUrls: ['./study-filters-block.component.css'],
})
export class StudyFiltersBlockComponent extends StatefulComponent implements OnInit {
  @Input() public dataset: Dataset;
  public allStudies: Set<string>;

  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedStudies: Set<string> = new Set();

  @ViewChild('nav') public ngbNav: NgbNav;

  public constructor(protected store: Store) {
    super(store, StudyFiltersBlockState, 'studyFilters');
  }

  public ngOnInit(): void {
    super.ngOnInit();

    this.allStudies = new Set<string>(this.dataset.studyNames);

    this.store.selectOnce(state => state.studyFiltersBlockState as StudyFiltersBlockModel).subscribe(state => {
      // restore state
      if (state.studyFilters.length !== 0) {
        this.updateSelectedStudies(new Set(state.studyFilters))
        setTimeout(() => this.ngbNav.select('studyNames'));
      } else {
        this.updateSelectedStudies(new Set(this.allStudies));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(new SetStudyFilters([]));
    this.store.dispatch(new StateReset(StudyFiltersBlockState));
    this.selectedStudies = new Set(this.allStudies);
  }

  public updateSelectedStudies(newValues: Set<string>): void {
    this.selectedStudies = newValues;
    this.store.dispatch(new SetStudyFilters(Array.from(newValues)));
  }
}
