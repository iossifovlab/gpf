import { Component, AfterViewInit, Input, ViewChild, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store, Selector } from '@ngxs/store';
import { FamilyIdsModel, FamilyIdsState } from 'app/family-ids/family-ids.state';
import { PersonFiltersModel, PersonFiltersState, SetFamilyFilters } from 'app/person-filters/person-filters.state';
import { StateReset } from 'ngxs-reset-plugin';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
})
export class FamilyFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() public dataset: Dataset;
  @Input() public genotypeBrowserState: object;
  @ViewChild('nav') public ngbNav: NgbNav;
  public showFamilyTypeFilter: boolean;
  public showAdvancedButton: boolean;

  public constructor(
    private store: Store,
  ) { }

  public ngOnInit(): void {
    this.showFamilyTypeFilter = this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;
    this.showAdvancedButton =
      this.dataset.genotypeBrowserConfig.familyFilters.length !== 0 ||
      this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;
  }

  public ngAfterViewInit(): void {
    this.store.selectOnce(FamilyFiltersBlockComponent.familyFiltersBlockState).subscribe(state => {
      if (state['familyIds']) {
        setTimeout(() => this.ngbNav.select('familyIds'));
      } else if (state['familyFilters']) {
        setTimeout(() => this.ngbNav.select('advanced'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(new SetFamilyFilters([]));
    this.store.dispatch(new StateReset(FamilyIdsState));
  }

  @Selector([FamilyIdsState, PersonFiltersState])
  public static familyFiltersBlockState(
    familyIdsState: FamilyIdsModel, personFiltersState: PersonFiltersModel
  ): object {
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
