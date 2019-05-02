import { Component, OnChanges, SimpleChanges, Input } from '@angular/core';
import { CategoricalFilterState, CategoricalSelection } from '../pheno-filters/pheno-filters';
import { PhenoFilter } from '../datasets/datasets';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-categorical-filter',
  templateUrl: './categorical-filter.component.html',
  styleUrls: ['./categorical-filter.component.css']
})
export class CategoricalFilterComponent implements OnChanges {
  @Input() categoricalFilter: PhenoFilter;
  @Input() categoricalFilterState: CategoricalFilterState;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
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
    let phenoFilterState = state
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
