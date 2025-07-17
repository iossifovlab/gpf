import { Component, Input, OnInit } from '@angular/core';
import { CategoricalFilterState, CategoricalSelection, PersonFilterState } from '../person-filters/person-filters';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Observable, switchMap, take } from 'rxjs';
import { environment } from 'environments/environment';
import { Store } from '@ngrx/store';
import { selectDatasetId } from 'app/datasets/datasets.state';
import {
  removeFamilyFilter,
  removePersonFilter,
  selectPersonFilters,
  updateFamilyFilter,
  updatePersonFilter
} from 'app/person-filters/person-filters.state';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-categorical-filter',
  templateUrl: './categorical-filter.component.html',
  styleUrls: ['./categorical-filter.component.css'],
  standalone: false
})
export class CategoricalFilterComponent implements OnInit {
  @Input() public categoricalFilter: PersonFilterState;
  @Input() public isFamilyFilters: boolean;
  public categoricalFilterState: CategoricalFilterState;
  public sourceDescription$: Observable<object>;
  public valuesDomain: any = [];
  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    private datasetsService: DatasetsService,
    private phenoBrowserService: PhenoBrowserService,
    private store: Store
  ) {}

  public ngOnInit(): void {
    this.store.select(selectPersonFilters).pipe(
      take(1),
      switchMap(state => {
        let stateFilter: CategoricalFilterState;

        if (this.isFamilyFilters) {
          stateFilter = state.familyFilters?.find(filter => filter.id === this.categoricalFilter.id);
        } else {
          stateFilter = state.personFilters?.find(filter => filter.id === this.categoricalFilter.id);
        }

        if (stateFilter) {
          this.categoricalFilterState = cloneDeep(stateFilter);
        } else {
          this.categoricalFilterState = cloneDeep(this.categoricalFilter);
        }

        return this.store.select(selectDatasetId).pipe(take(1));
      }),
      switchMap((datasetIdState: string) => {
        const selectedDatasetId = datasetIdState;

        if (this.categoricalFilterState.from === 'phenodb') {
          this.sourceDescription$ = this.phenoBrowserService.getMeasureDescription(
            selectedDatasetId, this.categoricalFilterState.source
          );
        } else if (this.categoricalFilterState.from === 'pedigree') {
          this.sourceDescription$ = this.datasetsService.getDatasetPedigreeColumnDetails(
            selectedDatasetId, this.categoricalFilterState.source
          );
        }
        return this.sourceDescription$;
      })
    ).subscribe(res => {
      this.valuesDomain = res['values_domain'];
    });
  }

  public set selectedValue(value) {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [value];
    if (this.isFamilyFilters) {
      this.store.dispatch(updateFamilyFilter({familyFilter: cloneDeep(this.categoricalFilterState)}));
    } else {
      this.store.dispatch(updatePersonFilter({personFilter: cloneDeep(this.categoricalFilterState)}));
    }
  }

  public get selectedValue(): string {
    return (this.categoricalFilterState.selection as CategoricalSelection).selection[0];
  }

  public clear(): void {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [];
    if (this.isFamilyFilters) {
      this.store.dispatch(removeFamilyFilter({familyFilter: cloneDeep(this.categoricalFilterState)}));
    } else {
      this.store.dispatch(removePersonFilter({personFilter: cloneDeep(this.categoricalFilterState)}));
    }
  }
}
