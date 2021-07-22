import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { QueryService } from '../query/query.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Store } from '@ngxs/store';
import { StateReset } from 'ngxs-reset-plugin';
import { ErrorsState } from 'app/common/errors.state';
import { take } from 'rxjs/operators';

const PAGE_TYPE_TO_NAVIGATE = {
    genotype: datasetId => ['datasets', datasetId, 'genotype-browser'],
    phenotype: datasetId => ['datasets', datasetId, 'phenotype-browser'],
    enrichment: datasetId => ['datasets', datasetId, 'enrichment-tool'],
    phenotool: datasetId => ['datasets', datasetId, 'phenotype-tool']
};

@Component({
  selector: 'gpf-load-query',
  templateUrl: './load-query.component.html',
  styleUrls: ['./load-query.component.css']
})
export class LoadQueryComponent implements OnInit {

  constructor(
    private store: Store,
    private queryService: QueryService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit() {
      this.route.params.subscribe(
          params => {
              if (!params['uuid']) {
                  this.router.navigate(['/']);
              } else {
                  this.loadQuery(params['uuid']);
              }
          });
  }

  private loadQuery(uuid: string) {
      this.queryService.loadQuery(uuid)
          .pipe(take(1))
          .subscribe(response => {
              const queryData = response['data'];
              const page = response['page'];
              this.restoreQuery(queryData, page);
          });
  }

  private restoreQuery(state: {}, page: string) {
      if (page in PAGE_TYPE_TO_NAVIGATE) {
          const navigationParams = PAGE_TYPE_TO_NAVIGATE[page](state['datasetId']);
          this.store.reset(state);
          this.store.dispatch(new StateReset(ErrorsState));
          this.router.navigate(navigationParams);
      }
  }

}
