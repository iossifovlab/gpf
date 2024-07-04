import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { QueryService } from '../query/query.service';
import { Store } from '@ngxs/store';
import { StateReset } from 'ngxs-reset-plugin';
import { ErrorsState } from 'app/common/errors.state';
import { take } from 'rxjs/operators';

const PAGE_TYPE_TO_NAVIGATE = {
  genotype: (datasetId: string): string[] => ['datasets', datasetId, 'genotype-browser'],
  phenotype: (datasetId: string): string[] => ['datasets', datasetId, 'phenotype-browser'],
  enrichment: (datasetId: string): string[] => ['datasets', datasetId, 'enrichment-tool'],
  phenotool: (datasetId: string): string[] => ['datasets', datasetId, 'phenotype-tool']
};

@Component({
  selector: 'gpf-load-query',
  templateUrl: './load-query.component.html',
  styleUrls: ['./load-query.component.css']
})
export class LoadQueryComponent implements OnInit {
  public constructor(
    private store: Store,
    private queryService: QueryService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  public ngOnInit(): void {
    this.route.params.subscribe(
      params => {
        if (!params['uuid']) {
          this.router.navigate(['/']);
        } else {
          this.loadQuery(params['uuid'] as string);
        }
      });
  }

  private loadQuery(uuid: string): void {
    this.queryService.loadQuery(uuid)
      .pipe(take(1))
      .subscribe(response => {
        const queryData = response['data'] as object;
        const page = response['page'] as string;
        this.restoreQuery(queryData, page);
      });
  }

  private restoreQuery(state: object, page: string): void {
    if (page in PAGE_TYPE_TO_NAVIGATE) {
      const navigationParams: string[] = PAGE_TYPE_TO_NAVIGATE[page](state['datasetState'].selectedDatasetId);
      this.store.reset(state);
      this.store.dispatch(new StateReset(ErrorsState));
      this.router.navigate(navigationParams);
    }
  }
}
