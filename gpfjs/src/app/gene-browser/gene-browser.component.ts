import { Component, OnInit, OnChanges, AfterViewInit, SimpleChanges } from '@angular/core';
import { GeneService } from 'app/gene-view/gene.service';
import { Gene } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray, GenotypePreviewInfo } from 'app/genotype-preview-model/genotype-preview';
import { QueryService } from 'app/query/query.service';
import { Observable } from 'rxjs';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { ActivatedRoute, Params } from '@angular/router';
import { QueryStateCollector } from 'app/query/query-state-provider';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';

@Component({
  selector: 'gpf-gene-browser-component',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: GeneBrowserComponent
  }]
})
export class GeneBrowserComponent extends QueryStateCollector
implements OnInit {
  selectedGene: Gene;
  geneSymbol: string = 'CHD8';
  genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  selectedDataset$: Observable<Dataset>;
  selectedDatasetId: string;
  genotypePreviewInfo: GenotypePreviewInfo;
  loadingFinished: boolean;
  private genotypeBrowserState: Object;

  constructor(
    public queryService: QueryService,
    private geneService: GeneService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private loadingService: FullscreenLoadingService

  ) {
    super();
  }

  ngOnInit() {
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();

    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params['dataset'];
      }
     );
  }

  getCurrentState() {
    const state = super.getCurrentState();
    return state.map(current_state => {
      const stateObject = Object.assign({ datasetId: this.selectedDatasetId }, current_state);
      return stateObject;
    });
  }

  submitGeneRequest() {

    this.getCurrentState()
      .subscribe(state => {
        this.geneSymbol = state["geneSymbols"][0];

        this.geneService.getGene(this.geneSymbol.toUpperCase().trim()).subscribe((gene) => {
          this.selectedGene = gene;
        });

        this.genotypePreviewInfo = null;
        this.loadingFinished = false;
        this.loadingService.setLoadingStart();
        this.queryService.getGenotypePreviewInfo(
          { datasetId: this.selectedDatasetId, peopleGroup: state["peopleGroup"] }
        ).subscribe(
          (genotypePreviewInfo) => {
            this.genotypePreviewInfo = genotypePreviewInfo;
            this.genotypePreviewVariantsArray = null;

            this.genotypeBrowserState = state;

            this.queryService.streamingFinishedSubject.subscribe(
              _ => { this.loadingFinished = true; }
            );

            this.genotypePreviewVariantsArray =
              this.queryService.getGenotypePreviewVariantsByFilter(
                state, this.genotypePreviewInfo, this.loadingService
              );

          }, error => {
            console.warn(error);
          }
        );
      }, error => {
        console.error(error);
      });
  }
}
