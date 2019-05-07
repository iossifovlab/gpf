import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { QueryService } from '../query/query.service';
import { StateRestoreService } from '../store/state-restore.service';
import { DatasetsService } from '../datasets/datasets.service';

const PAGE_TYPE_TO_NAVIGATE = {
    genotype: datasetId => ['datasets', datasetId, 'browser'],
    phenotype: datasetId => ['datasets', datasetId, 'phenotypeBrowser'],
    enrichment: datasetId => ['datasets', datasetId, 'enrichment'],
    phenotool: datasetId => ['datasets', datasetId, 'phenoTool']
};

@Component({
  selector: 'gpf-load-query',
  templateUrl: './load-query.component.html',
  styleUrls: ['./load-query.component.css']
})
export class LoadQueryComponent implements OnInit {

  constructor(
    private queryService: QueryService,
    private stateRestoreService: StateRestoreService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit() {
      console.log('LoadQueryComponent loaded');
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
          .take(1)
          .subscribe(response => {
              let queryData = response['data'];
              let page = response['page'];

              this.restoreQuery(queryData, page);
          });
  }

  private restoreQuery(queryData: {}, page: string) {
      console.log(queryData, page);
      if (page in PAGE_TYPE_TO_NAVIGATE) {
          let navigationParams = 
              PAGE_TYPE_TO_NAVIGATE[page](queryData['datasetId']);
          this.stateRestoreService.pushNewState(queryData);
          this.router.navigate(navigationParams);
      }
  }

}
