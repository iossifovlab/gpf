import { Component, AfterViewInit, Input, ViewChild, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store, Selector } from '@ngxs/store';
import { PersonIdsState } from 'app/person-ids/person-ids.state';
import { PersonFiltersState } from 'app/person-filters/person-filters.state';
import { StateReset } from 'ngxs-reset-plugin';


@Component({
  selector: 'gpf-person-filters-block',
  templateUrl: './person-filters-block.component.html',
  styleUrls: ['./person-filters-block.component.css'],
})
export class PersonFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() dataset: Dataset;
  @Input() genotypeBrowserState: Object;
  @ViewChild('nav') ngbNav;
  showAdvancedButton: boolean;

  constructor(private store: Store) { }

  @Selector([PersonIdsState, PersonFiltersState])
  static personFiltersBlockState(personIdsState, personFiltersState) {
    const res = {};
    if (personIdsState.personIds.length) {
      res['personIds'] = personIdsState.personIds;
    }
    if (personFiltersState.personFilters.length) {
      res['personFilters'] = personFiltersState.personFilters;
    }
    return res;
  }

  ngOnInit(): void {
    this.showAdvancedButton = this.dataset.genotypeBrowserConfig.personFilters.length !== 0;
  }

  ngAfterViewInit() {
    this.store.selectOnce(PersonFiltersBlockComponent.personFiltersBlockState).subscribe(state => {
      if (state['personIds']) {
        setTimeout(() => this.ngbNav.select('personIds'));
      } else if (state['personFilters']) {
        setTimeout(() => this.ngbNav.select('advanced'));
      }
    });
  }

  onNavChange() {
    this.store.dispatch(new StateReset(PersonIdsState, PersonFiltersState));
  }

}
