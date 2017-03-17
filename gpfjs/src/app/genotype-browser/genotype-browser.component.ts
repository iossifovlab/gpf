import { Component } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider'
import { Observable } from 'rxjs';
import { Store } from '@ngrx/store';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import 'rxjs/add/operator/zip';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
})
export class GenotypeBrowserComponent extends QueryStateCollector {
  genotypePreviewsArray: any;


  constructor(
    private store: Store<any>,
    private queryService: QueryService,
    private configService: ConfigService,
    private loadingService: FullscreenLoadingService
  ) {
    super();
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({}, {datasetId: "SD"} , ...state);
        this.queryService.getGenotypePreviewByFilter(queryData).subscribe(
          (genotypePreviewsArray) => {
            this.genotypePreviewsArray = genotypePreviewsArray;
            this.loadingService.setLoadingStop();
          });
      },
      error => null
    )
  }

  onSubmit(event) {
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({}, ...state);
        event.target.queryData.value = JSON.stringify(queryData);
        event.target.submit();
        console.log(Object.assign({}, ...state))
      },
      error => null
    )
  }
}
