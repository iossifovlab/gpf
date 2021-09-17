import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
// tslint:disable-next-line:import-blacklist
import { Observable, Subject } from 'rxjs';

const oboe = require('oboe');

import { environment } from 'environments/environment';
import { ConfigService } from '../config/config.service';
import { GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';
import { SummaryAllelesArray } from '../gene-browser/summary-variants';
import { DatasetsService } from 'app/datasets/datasets.service';
import { map } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';

@Injectable()
export class QueryService {
  private readonly genotypeBrowserConfigUrl = 'genotype_browser/config';
  private readonly genotypePreviewVariantsUrl = 'genotype_browser/query';
  private readonly geneViewVariants = 'gene_view/query_summary_variants';
  private readonly saveQueryEndpoint = 'query_state/save';
  private readonly loadQueryEndpoint = 'query_state/load';
  private readonly deleteQueryEndpoint = 'query_state/delete';
  private readonly userSaveQueryEndpoint = 'user_queries/save';
  private readonly userCollectQueriesEndpoint = 'user_queries/collect';

  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  private oboeInstance = null;
  private summaryOboeInstance = null;
  public streamingSubject = new Subject();
  public summaryStreamingSubject = new Subject();
  public streamingFinishedSubject = new Subject();
  public summaryStreamingFinishedSubject = new Subject();

  constructor(
    private location: Location,
    private router: Router,
    private http: HttpClient,
    private config: ConfigService,
    private datasetsService: DatasetsService,
  ) { }

  public streamPost(url: string, filter) {
    if (this.oboeInstance) {
      this.oboeInstance.abort();
      this.oboeInstance = null;
    }

    this.oboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: filter,
      withCredentials: true
    }).node('!.*', data => {
      this.streamingSubject.next(data);
    }).done(data => {
      this.streamingFinishedSubject.next(true);
      // Emit null so the loading service can stop the loading overlay even if no variants were received
      this.streamingSubject.next(null);
    }).fail(error => {
      console.warn('oboejs encountered a fail event while streaming');
      console.error(error);
      this.streamingFinishedSubject.next(true);
      this.streamingSubject.next(null);
    });

    return this.streamingSubject;
  }

  public summaryStreamPost(url: string, filter) {
    if (this.summaryOboeInstance) {
      this.summaryOboeInstance.abort();
      this.summaryOboeInstance = null;
    }

    this.summaryOboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: filter,
      withCredentials: true
    }).node('!.*', data => {
      this.summaryStreamingSubject.next(data);
    }).done(data => {
      this.summaryStreamingFinishedSubject.next(true);
      this.summaryStreamingSubject.next(null);
    }).fail(error => {
      console.warn('oboejs encountered a fail event while streaming');
      console.error(error);
      this.summaryStreamingFinishedSubject.next(true);
      this.summaryStreamingSubject.next(null);
    });

    return this.summaryStreamingSubject;
  }

  getGenotypePreviewVariantsByFilter(
    dataset: Dataset, filter, loadingService?: any, maxVariantsCount: number = 1001
  ): GenotypePreviewVariantsArray {
    const genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();
    const queryFilter = { ...filter };
    queryFilter['maxVariantsCount'] = maxVariantsCount;

    this.streamPost(this.genotypePreviewVariantsUrl, queryFilter).subscribe(variant => {
      genotypePreviewVariantsArray.addPreviewVariant(
        <Array<string>> variant,
        dataset.genotypeBrowserConfig.columnIds
      );

      if (variant) {
        // Attach the genome version to each variant
        // This is done so that the table can construct the correct UCSC link for the variant
        genotypePreviewVariantsArray.genotypePreviews[
          genotypePreviewVariantsArray.genotypePreviews.length - 1
        ].data.set('genome', dataset.genome);
      }
      if (loadingService) {
        loadingService.setLoadingStop(); // Stop the loading overlay when at least one variant has been loaded
      }
    });

    return genotypePreviewVariantsArray;
  }

  getSummaryVariants(filter) {
    const summaryVariantsArray = new SummaryAllelesArray();
    this.summaryStreamPost(this.geneViewVariants, filter).subscribe((variant: string[]) => {
      summaryVariantsArray.addSummaryRow(variant);
    });
    return summaryVariantsArray;
  }

  saveQuery(queryData: {}, page: string) {
    const options = { headers: this.headers };

    queryData = {...queryData};
    delete queryData['errorsState'];

    const data = {
      data: queryData,
      page: page
    };

    return this.http
      .post(this.config.baseUrl + this.saveQueryEndpoint, data, options)
      .pipe(map(response => response));
  }

  loadQuery(uuid: string) {
    const options = { headers: this.headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.loadQueryEndpoint, { uuid: uuid }, options)
      .pipe(map(response => response));
  }

  deleteQuery(uuid: string) {
    const options = { headers: this.headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.deleteQueryEndpoint, { uuid: uuid }, options)
      .pipe(map(response => response));
  }

  getLoadUrl(uuid: string) {
    let pathname = this.router.createUrlTree(
      ['load-query', uuid]).toString();
    pathname = this.location.prepareExternalUrl(pathname);

    return window.location.origin + pathname;
  }

  getLoadUrlFromResponse(response: {}) {
    return this.getLoadUrl(response['uuid']);
  }

  saveUserQuery(uuid: string, query_name: string, query_description: string) {
    const options = { headers: this.headers, withCredentials: true };

    const data = {
      query_uuid: uuid,
      name: query_name,
      description: query_description
    };

    return this.http
      .post(this.config.baseUrl + this.userSaveQueryEndpoint, data, options)
      .pipe(map(response => response));
  }

  collectUserSavedQueries() {
    const options = { withCredentials: true };
    return this.http
      .get(this.config.baseUrl + this.userCollectQueriesEndpoint, options)
      .pipe(map(response => response));
  }
}
