import { Component, AfterViewInit, Input, ViewChild, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngrx/store';
import { resetPersonFilterStates, selectPersonFilters } from 'app/person-filters/person-filters.state';
import { combineLatest, take } from 'rxjs';
import { resetPersonIds, selectPersonIds } from 'app/person-ids/person-ids.state';

@Component({
  selector: 'gpf-person-filters-block',
  templateUrl: './person-filters-block.component.html',
  styleUrls: ['./person-filters-block.component.css'],
})
export class PersonFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() public dataset: Dataset;
  @ViewChild('nav') public ngbNav: NgbNav;
  public showAdvancedButton: boolean;
  public showAdvancedBetaButton: boolean;

  public constructor(private store: Store) { }

  public ngOnInit(): void {
    this.showAdvancedButton = this.dataset.genotypeBrowserConfig.personFilters.length !== 0;
    this.showAdvancedBetaButton = this.dataset.genotypeBrowserConfig.hasPersonFiltersBeta;
  }

  public ngAfterViewInit(): void {
    combineLatest([
      this.store.select(selectPersonFilters),
      this.store.select(selectPersonIds),
    ]).pipe(take(1)).subscribe(([personFiltersState, personIdsState]) => {
      if (personIdsState.length) {
        setTimeout(() => this.ngbNav.select('personIds'));
      } else if (personFiltersState?.personFilters?.length) {
        setTimeout(() => this.ngbNav.select('advanced'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(resetPersonIds());
    this.store.dispatch(resetPersonFilterStates());
  }
}
