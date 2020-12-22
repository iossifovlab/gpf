import { Component, OnChanges, SimpleChanges, Input, OnInit } from '@angular/core';
import { CategoricalFilterState, CategoricalSelection } from '../pheno-filters/pheno-filters';
import { PhenoFilter } from '../datasets/datasets';
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
  @Input() categoricalFilter: PhenoFilter;
  @Input() categoricalFilterState: CategoricalFilterState;
  measureDescription$: Observable<Object>;

  constructor(
    private datasetsService: DatasetsService,
    private phenoBrowserService: PhenoBrowserService,
    private stateRestoreService: StateRestoreService,
  ) {
  }

  ngOnInit(): void {
    this.measureDescription$ = this.phenoBrowserService.getMeasureDesciption(
      this.datasetsService.getSelectedDatasetId(), this.categoricalFilter.measure
    );
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
