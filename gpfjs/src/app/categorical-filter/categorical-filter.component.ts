import { Component, Input, OnInit, Output, EventEmitter } from '@angular/core';
import { CategoricalFilterState, CategoricalSelection } from '../person-filters/person-filters';
import { PersonFilter } from '../datasets/datasets';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Observable, switchMap, take } from 'rxjs';
import { environment } from 'environments/environment';
import { Store } from '@ngrx/store';
import { DatasetModel, selectDatasetId } from 'app/datasets/datasets.state';

@Component({
  selector: 'gpf-categorical-filter',
  templateUrl: './categorical-filter.component.html',
  styleUrls: ['./categorical-filter.component.css']
})
export class CategoricalFilterComponent implements OnInit {
  @Input() public categoricalFilter: PersonFilter;
  @Input() public categoricalFilterState: CategoricalFilterState;
  @Output() public updateFilterEvent = new EventEmitter();
  public sourceDescription$: Observable<object>;
  public valuesDomain: any = [];
  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    private datasetsService: DatasetsService,
    private phenoBrowserService: PhenoBrowserService,
    private store: Store
  ) {}

  public ngOnInit(): void {
    this.store.select(selectDatasetId).pipe(take(1)).subscribe(datasetId => {
      const selectedDatasetId = datasetId;

      if (this.categoricalFilter.from === 'phenodb') {
        this.sourceDescription$ = this.phenoBrowserService.getMeasureDescription(
          selectedDatasetId, this.categoricalFilter.source
        );
      } else if (this.categoricalFilter.from === 'pedigree') {
        this.sourceDescription$ = this.datasetsService.getDatasetPedigreeColumnDetails(
          selectedDatasetId, this.categoricalFilter.source
        );
      }

      this.sourceDescription$.pipe(take(1)).subscribe(res => {
        this.valuesDomain = res['values_domain'];
      });
    });

    // this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
    //   switchMap((state: DatasetModel) => {
    //     const selectedDatasetId = state.selectedDatasetId;

    //     if (this.categoricalFilter.from === 'phenodb') {
    //       this.sourceDescription$ = this.phenoBrowserService.getMeasureDescription(
    //         selectedDatasetId, this.categoricalFilter.source
    //       );
    //     } else if (this.categoricalFilter.from === 'pedigree') {
    //       this.sourceDescription$ = this.datasetsService.getDatasetPedigreeColumnDetails(
    //         selectedDatasetId, this.categoricalFilter.source
    //       );
    //     }
    //     return this.sourceDescription$;
    //   })
    // ).subscribe(res => {
    //   this.valuesDomain = res['values_domain'];
    // });
  }

  public set selectedValue(value) {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [value];
    this.updateFilterEvent.emit();
  }

  public get selectedValue(): string {
    return (this.categoricalFilterState.selection as CategoricalSelection).selection[0];
  }

  public clear(): void {
    (this.categoricalFilterState.selection as CategoricalSelection).selection = [];
    this.updateFilterEvent.emit();
  }
}
