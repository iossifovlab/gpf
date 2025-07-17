import { Component, AfterViewInit, Input, ViewChild, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngrx/store';
import { resetPersonFilterStates, selectPersonFilters } from 'app/person-filters/person-filters.state';
import { combineLatest, take } from 'rxjs';
import { resetPersonIds, selectPersonIds } from 'app/person-ids/person-ids.state';
import {
  resetPersonMeasureHistograms,
  selectPersonMeasureHistograms
} from 'app/person-filters-selector/measure-histogram.state';

@Component({
  selector: 'gpf-person-filters-block',
  templateUrl: './person-filters-block.component.html',
  styleUrls: ['./person-filters-block.component.css'],
  standalone: false
})
export class PersonFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() public dataset: Dataset;
  @ViewChild('nav') public ngbNav: NgbNav;
  public showAdvancedButton: boolean;
  public showPhenoMeasuresButton: boolean;

  public constructor(private store: Store) { }

  public ngOnInit(): void {
    this.showAdvancedButton = this.dataset.genotypeBrowserConfig.personFilters.length !== 0;
    this.showPhenoMeasuresButton = this.dataset.genotypeBrowserConfig.hasPersonPhenoFilters;
  }

  public ngAfterViewInit(): void {
    combineLatest([
      this.store.select(selectPersonFilters),
      this.store.select(selectPersonIds),
      this.store.select(selectPersonMeasureHistograms),
    ]).pipe(take(1)).subscribe(([personFiltersState, personIdsState, personMeasureHistograms]) => {
      if (personIdsState.length) {
        setTimeout(() => this.ngbNav.select('personIds'));
      } else if (personFiltersState?.personFilters?.length) {
        setTimeout(() => this.ngbNav.select('advanced'));
      } else if (personMeasureHistograms?.length) {
        setTimeout(() => this.ngbNav.select('phenoMeasures'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(resetPersonIds());
    this.store.dispatch(resetPersonFilterStates());
    this.store.dispatch(resetPersonMeasureHistograms());
  }
}
