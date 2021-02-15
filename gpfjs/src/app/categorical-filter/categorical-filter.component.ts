import { Component, OnChanges, SimpleChanges, Input, OnInit } from '@angular/core';
import { CategoricalFilterState, CategoricalSelection } from '../person-filters/person-filters';
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
  sourceDescription$: Observable<Object>;
  valuesDomain: any = [];

  constructor(
    private datasetsService: DatasetsService,
    private phenoBrowserService: PhenoBrowserService,
    private stateRestoreService: StateRestoreService,
  ) {
  }

  ngOnInit(): void {

    if (this.categoricalFilter.from === 'phenodb') {
      this.sourceDescription$ = this.phenoBrowserService.getMeasureDescription(
        this.datasetsService.getSelectedDatasetId(), this.categoricalFilter.source
      );
    } else if (this.categoricalFilter.from === 'pedigree') {
      this.sourceDescription$ = this.datasetsService.getDatasetPedigreeColumnDetails(
        this.datasetsService.getSelectedDatasetId(), this.categoricalFilter.source
      );
    }
    this.sourceDescription$.subscribe(res => {
      this.valuesDomain = res['values_domain'];
    });
  }

  ngOnChanges(change: SimpleChanges) {
    if (change['categoricalFilterState'] && change['categoricalFilterState'].isFirstChange()) {
      this.stateRestoreService
        .getState(this.constructor.name + this.categoricalFilterState.id)
        .take(1)
        .subscribe(state => {
          if (state['personFilters']) {
            this.restoreCategoricalFilter(state['personFilters']);
          }
        });
    }
  }

  restoreCategoricalFilter(state) {
    const personFilterState = state.find(f => f.id === this.categoricalFilterState.id);
    if (personFilterState) {
      this.categoricalFilterState.selection = personFilterState.selection.slice();
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
