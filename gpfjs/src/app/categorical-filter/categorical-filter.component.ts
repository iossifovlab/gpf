import { Component, Input, OnInit, Output, EventEmitter } from '@angular/core';
import { CategoricalFilterState, CategoricalSelection } from '../person-filters/person-filters';
import { PersonFilter } from '../datasets/datasets';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Observable } from 'rxjs';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-categorical-filter',
  templateUrl: './categorical-filter.component.html',
  styleUrls: ['./categorical-filter.component.css']
})
export class CategoricalFilterComponent implements OnInit {
  @Input() categoricalFilter: PersonFilter;
  @Input() categoricalFilterState: CategoricalFilterState;
  @Output() updateFilterEvent = new EventEmitter();
  sourceDescription$: Observable<Object>;
  valuesDomain: any = [];
  public imgPathPrefix = environment.imgPathPrefix;

  constructor(
    private datasetsService: DatasetsService,
    private phenoBrowserService: PhenoBrowserService,
  ) {
  }

  ngOnInit(): void {
    if (this.categoricalFilter.from === 'phenodb') {
      this.sourceDescription$ = this.phenoBrowserService.getMeasureDescription(
        this.datasetsService.getSelectedDataset().id, this.categoricalFilter.source
      );
    } else if (this.categoricalFilter.from === 'pedigree') {
      this.sourceDescription$ = this.datasetsService.getDatasetPedigreeColumnDetails(
        this.datasetsService.getSelectedDataset().id, this.categoricalFilter.source
      );
    }
    this.sourceDescription$.subscribe(res => {
      this.valuesDomain = res['values_domain'];
    });
  }

  set selectedValue(value) {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [value];
    this.updateFilterEvent.emit();
  }

  get selectedValue(): string {
    return (this.categoricalFilterState.selection as CategoricalSelection).selection[0];
  }

  clear() {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [];
    this.updateFilterEvent.emit();
  }
}
