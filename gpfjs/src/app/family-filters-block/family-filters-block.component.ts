import { Component, AfterViewInit, Input, ViewChild, OnInit } from '@angular/core';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { Store, Selector } from '@ngxs/store';
import { FamilyIdsState } from 'app/family-ids/family-ids.state';
import { PersonFiltersState } from 'app/person-filters/person-filters.state';
import { StateReset } from 'ngxs-reset-plugin';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
})
export class FamilyFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() dataset: Dataset;
  @Input() genotypeBrowserState: Object;
  @ViewChild('nav') ngbNav;
  showFamilyTypeFilter: boolean;
  showAdvancedButton: boolean;

  constructor(
    private store: Store,
    private datasetsService: DatasetsService,
  ) { }

  ngOnInit(): void {
    this.showFamilyTypeFilter = this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;
    this.showAdvancedButton =
      this.dataset.genotypeBrowserConfig.familyFilters.length !== 0 ||
      this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;
  }

  ngAfterViewInit() {
    this.store.selectOnce(FamilyFiltersBlockComponent.familyFiltersBlockState).subscribe(state => {
      if (state['familyIds']) {
        setTimeout(() => this.ngbNav.select('familyIds'));
      } else if (state['familyFilters']) {
        setTimeout(() => this.ngbNav.select('advanced'));
      }
    });
  }

  onNavChange() {
    this.store.dispatch(new StateReset(FamilyIdsState, PersonFiltersState));
  }

  @Selector([FamilyIdsState, PersonFiltersState])
  static familyFiltersBlockState(familyIdsState, personFiltersState) {
    const res = {};
    if (familyIdsState.familyIds.length) {
      res['familyIds'] = familyIdsState.familyIds;
    }
    if (personFiltersState.familyFilters.length) {
      res['familyFilters'] = personFiltersState.familyFilters;
    }
    return res;
  }
}
