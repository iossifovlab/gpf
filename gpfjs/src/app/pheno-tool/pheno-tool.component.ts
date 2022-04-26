import { Component, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
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
import { ErrorsState, ErrorsModel } from 'app/common/errors.state';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css'],
})
export class PhenoToolComponent implements OnInit {
  @Select(PhenoToolComponent.phenoToolStateSelector) public state$: Observable<object[]>;
  @Select(ErrorsState) public errorsState$: Observable<ErrorsModel>;

  public selectedDataset: Dataset;

  public phenoToolResults: PhenoToolResults;
  public phenoToolState: object;

  public disableQueryButtons = false;

  public constructor(
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private phenoToolService: PhenoToolService,
    public readonly configService: ConfigService,
  ) { }

  @Selector([
    GenesBlockComponent.genesBlockState,
    PhenoToolMeasureState,
    PhenoToolGenotypeBlockComponent.phenoToolGenotypeBlockQueryState,
    FamilyFiltersBlockComponent.familyFiltersBlockState,
  ])
  public static phenoToolStateSelector(
    genesBlockState: object, measureState: object, genotypeState: object, familyFiltersState: object
  ): object {
    return {
      ...genesBlockState,
      ...measureState,
      ...genotypeState,
      ...familyFiltersState,
    };
  }

  public ngOnInit(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();

    this.state$.subscribe(state => {
      this.phenoToolState = state;
      this.phenoToolResults = null;
    });

    this.errorsState$.subscribe(state => {
      setTimeout(() => {
        this.disableQueryButtons = state.componentErrors.size > 0;
      });
    });
  }

  public submitQuery(): void {
    this.loadingService.setLoadingStart();
    this.phenoToolService.getPhenoToolResults(
      {datasetId: this.selectedDataset.id, ...this.phenoToolState}
    ).subscribe((phenoToolResults) => {
      this.phenoToolResults = phenoToolResults;
      this.loadingService.setLoadingStop();
    }, () => {
      this.loadingService.setLoadingStop();
    }, () => {
      this.loadingService.setLoadingStop();
    });
  }

  public onDownload(event: Event): void {
    if (event.target instanceof HTMLFormElement) {
      event.target.queryData.value = JSON.stringify({...this.phenoToolState, datasetId: this.selectedDataset.id});
      event.target.submit();
    }
  }
}
