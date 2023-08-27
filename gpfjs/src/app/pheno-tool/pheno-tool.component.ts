import { Component, OnDestroy, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { PhenoToolService } from './pheno-tool.service';
import { PhenoToolResults } from './pheno-tool-results';
import { ConfigService } from '../config/config.service';
import { Observable, Subscription } from 'rxjs';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { PhenoToolGenotypeBlockComponent } from 'app/pheno-tool-genotype-block/pheno-tool-genotype-block.component';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PhenoToolMeasureState } from 'app/pheno-tool-measure/pheno-tool-measure.state';
import { Select, Selector } from '@ngxs/store';
import { ErrorsState, ErrorsModel } from 'app/common/errors.state';
import { AuthService } from 'app/auth.service';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css'],
})
export class PhenoToolComponent implements OnInit, OnDestroy {
  @Select(PhenoToolComponent.phenoToolStateSelector) public state$: Observable<object[]>;
  @Select(ErrorsState) public errorsState$: Observable<ErrorsModel>;

  public selectedDataset: Dataset;

  public phenoToolResults: PhenoToolResults;
  public phenoToolState: object;

  public disableQueryButtons = false;

  private phenoToolSubscription: Subscription = null;

  public constructor(
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private phenoToolService: PhenoToolService,
    public readonly configService: ConfigService,
    private authService: AuthService,
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

    this.loadingService.interruptEvent.subscribe(_ => {
      if (this.phenoToolSubscription !== null) {
        this.phenoToolSubscription.unsubscribe();
        this.phenoToolSubscription = null;
      }
      this.loadingService.setLoadingStop();
      this.phenoToolResults = null;
    });

    this.errorsState$.subscribe(state => {
      setTimeout(() => {
        this.disableQueryButtons = state.componentErrors.size > 0;
      });
    });
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
  }

  public submitQuery(): void {
    this.phenoToolResults = null;
    this.loadingService.setLoadingStart();
    this.phenoToolSubscription = this.phenoToolService.getPhenoToolResults(
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
    event.target.access_token.value = this.authService.getAccessToken();
      event.target.submit();
    }
  }
}
