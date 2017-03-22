import { Component } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider'
import { Observable } from 'rxjs';
import { Store } from '@ngrx/store';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import 'rxjs/add/operator/zip';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
})
export class GenotypeBrowserComponent extends QueryStateCollector {
  genotypePreviewsArray: any;

  private selectedDatasetId: string;

  constructor(
    private store: Store<any>,
    private queryService: QueryService,
    private configService: ConfigService,
    private loadingService: FullscreenLoadingService,
    private route: ActivatedRoute,
    private router: Router
  ) {
    super();
  }

  ngAfterViewInit() {
    this.store.subscribe(
      (param) => {
        let state = this.collectState();
        Observable.zip(...state)
        .subscribe(
          state => {
            this.genotypePreviewsArray = null
            this.router.navigate(['.', Object.assign({}, ...state)], { relativeTo: this.route });
          },
          error => {
            this.genotypePreviewsArray = null
            console.log(error);
          }
        )
      }
    )
  }

  ngOnInit() {
    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params['dataset'];
      }
    );
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);

        this.router.navigate(['.', Object.assign({}, ...state)], { relativeTo: this.route });
        this.queryService.getGenotypePreviewByFilter(queryData).subscribe(
          (genotypePreviewsArray) => {
            this.genotypePreviewsArray = genotypePreviewsArray;
            this.loadingService.setLoadingStop();
          });
      },
      error => {
        console.log(error);
        this.loadingService.setLoadingStop();
      }
    )
  }

  onSubmit(event) {
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        event.target.queryData.value = JSON.stringify(queryData);
        event.target.submit();
        console.log(Object.assign({}, ...state))
      },
      error => null
    )
  }
}
