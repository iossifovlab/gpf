import { Component, OnChanges, SimpleChanges, Input, OnInit } from '@angular/core';
import { CategoricalFilterState, CategoricalSelection } from '../pheno-filters/pheno-filters';
import { PersonFilter } from '../datasets/datasets';
import { StateRestoreService } from '../store/state-restore.service';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-categorical-filter',
  templateUrl: './categorical-filter.component.html',
  styleUrls: ['./categorical-filter.component.css']
})
export class CategoricalFilterComponent implements OnInit, OnChanges {
  @Input() categoricalFilter: PersonFilter;
  @Input() categoricalFilterState: CategoricalFilterState;
  measureDescription$: Observable<Object>;
  valuesDomain: any;

  constructor(
    private datasetsService: DatasetsService,
    private phenoBrowserService: PhenoBrowserService,
    private stateRestoreService: StateRestoreService,
  ) {
  }

  ngOnInit(): void {
    this.measureDescription$ = this.phenoBrowserService.getMeasureDescription(
      this.datasetsService.getSelectedDatasetId(), this.categoricalFilter.source
    );

    // FIXME fix this?
    this.valuesDomain = this.measureDescription$.subscribe(res => res['values_domain']);
  }

  ngOnChanges(change: SimpleChanges) {
    if (change['categoricalFilterState'] && change['categoricalFilterState'].isFirstChange()) {
      this.stateRestoreService
        .getState(this.constructor.name + this.categoricalFilterState.id)
        .take(1)
        .subscribe(state => {
          if (state['phenoFilters']) {
            this.restoreCategoricalFilter(state['phenoFilters']);
          }
        });
    }
  }

  restoreCategoricalFilter(state) {
    const phenoFilterState = state
      .find(f => f.id === this.categoricalFilterState.id);
    if (phenoFilterState) {
      this.categoricalFilterState.selection =
        phenoFilterState.selection.slice();
    }
  }

  set selectedValue(value) {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [value];
  }

  get selectedValue(): string {
    return (this.categoricalFilterState.selection as CategoricalSelection).selection[0];
  }

  clear() {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [];
  }

}
