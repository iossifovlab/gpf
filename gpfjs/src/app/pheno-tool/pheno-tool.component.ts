import { Component, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { ActivatedRoute } from '@angular/router';
import { Dataset } from '../datasets/datasets';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { PhenoToolService } from './pheno-tool.service';
import { PhenoToolResults } from './pheno-tool-results';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { PhenoToolGenotypeBlockComponent } from 'app/pheno-tool-genotype-block/pheno-tool-genotype-block.component';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PhenoToolMeasureState } from 'app/pheno-tool-measure/pheno-tool-measure.state';
import { Select, Selector } from '@ngxs/store';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css'],
})
export class PhenoToolComponent implements OnInit {
  selectedDatasetId: string;
  selectedDataset: Dataset;

  @Select(PhenoToolComponent.phenoToolStateSelector) state$: Observable<any[]>;

  phenoToolResults: PhenoToolResults;
  private phenoToolState: Object;

  private disableQueryButtons = false;

  constructor(
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private phenoToolService: PhenoToolService,
    readonly configService: ConfigService,
  ) { }

  ngOnInit() {
    this.datasetsService.getSelectedDataset()
      .subscribe(dataset => {
        this.selectedDatasetId = dataset.id;
        this.selectedDataset = dataset;
      });

    this.state$.subscribe(state => {
      this.phenoToolState = state;
      this.phenoToolResults = null;
    })
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    this.phenoToolService.getPhenoToolResults(
      {'datasetId': this.selectedDatasetId, ...this.phenoToolState}
    ).subscribe((phenoToolResults) => {
      this.phenoToolResults = phenoToolResults;
      this.loadingService.setLoadingStop();
    }, error => {
      this.loadingService.setLoadingStop();
    }, () => {
      this.loadingService.setLoadingStop();
    });
  }

  onDownload(event) {
    event.target.queryData.value = JSON.stringify(this.phenoToolState);
    event.target.submit();
  }

  @Selector([
    GenesBlockComponent.genesBlockState,
    PhenoToolMeasureState,
    PhenoToolGenotypeBlockComponent.phenoToolGenotypeBlockQueryState,
    FamilyFiltersBlockComponent.familyFiltersBlockState,
  ])
  static phenoToolStateSelector(
    genesBlockState, measureState, genotypeState, familyFiltersState
  ) {
    return {
      ...genesBlockState,
      ...measureState,
      ...genotypeState,
      ...familyFiltersState,
    }
  }
}
