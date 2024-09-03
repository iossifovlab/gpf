import { Component, AfterViewInit, Input, ViewChild, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
// import { PersonIdsModel, PersonIdsState } from 'app/person-ids/person-ids.state';
// import { PersonFiltersModel, PersonFiltersState, SetPersonFilters } from 'app/person-filters/person-filters.state';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngrx/store';
import { resetPersonFilters, selectPersonFilters } from 'app/person-filters/person-filters.state';
import { combineLatest, take } from 'rxjs';
import { resetPersonIds, selectPersonIds } from 'app/person-ids/person-ids.state';

@Component({
  selector: 'gpf-person-filters-block',
  templateUrl: './person-filters-block.component.html',
  styleUrls: ['./person-filters-block.component.css'],
})
export class PersonFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() public dataset: Dataset;
  @Input() public genotypeBrowserState: object;
  @ViewChild('nav') public ngbNav: NgbNav;
  public showAdvancedButton: boolean;

  public constructor(private store: Store) { }

  public ngOnInit(): void {
    this.showAdvancedButton = this.dataset.genotypeBrowserConfig.personFilters.length !== 0;
  }

  public ngAfterViewInit(): void {
    combineLatest(
      this.store.select(selectPersonFilters),
      this.store.select(selectPersonIds),
    ).pipe(take(1)).subscribe(([personFiltersState, personIdsState]) => {
      if (personIdsState.length) {
        setTimeout(() => this.ngbNav.select('personIds'));
      } else if (personFiltersState.personFilters.length) {
        setTimeout(() => this.ngbNav.select('advanced'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(resetPersonFilters());
    this.store.dispatch(resetPersonIds());
  }
}
