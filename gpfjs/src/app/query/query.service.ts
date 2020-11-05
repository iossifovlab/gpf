import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
// tslint:disable-next-line:import-blacklist
import { Observable, Subject } from 'rxjs';

const oboe = require('oboe');

import { environment } from 'environments/environment';
import { QueryData } from './query';
import { ConfigService } from '../config/config.service';
import { GenotypePreviewInfo, GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';
import { GeneViewSummaryVariantsArray } from '../gene-view/gene';

@Injectable()
export class QueryService {
  private readonly genotypePreviewUrl = 'genotype_browser/preview';
  private readonly genotypePreviewVariantsUrl = 'genotype_browser/preview/variants';
  private readonly geneViewVariants = 'gene_view/query_summary_variants';
  private readonly saveQueryEndpoint = 'query_state/save';
  private readonly loadQueryEndpoint = 'query_state/load';
  private readonly deleteQueryEndpoint = 'query_state/delete';
  private readonly userSaveQueryEndpoint = 'user_queries/save';
  private readonly userCollectQueriesEndpoint = 'user_queries/collect';

  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  private connectionEstablished = false;
  private summaryConnectionEstablished = false;
  private oboeInstance = null;
  public streamingFinishedSubject = new Subject(); // This is for notifying that the streaming has completely finished
  public summaryStreamingFinishedSubject = new Subject(); // This is for notifying that the streaming has completely finished

  constructor(
    private location: Location,
    private router: Router,
    private http: HttpClient,
    private config: ConfigService
  ) { }

  private parseGenotypePreviewInfoResponse(response: Response): GenotypePreviewInfo {
    const data = response;
    const genotypePreviewInfoArray = GenotypePreviewInfo.fromJson(data);

    return genotypePreviewInfoArray;
  }

  private parseGenotypePreviewVariantsResponse(
    response: any, genotypePreviewInfo: GenotypePreviewInfo,
    genotypePreviewVariantsArray: GenotypePreviewVariantsArray) {
    genotypePreviewVariantsArray.addPreviewVariant(response, genotypePreviewInfo);
  }

  getGenotypePreviewInfo(filter: QueryData): Observable<GenotypePreviewInfo> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.genotypePreviewUrl, filter, options)
      .map(this.parseGenotypePreviewInfoResponse);
  }

  streamPost(url: string, filter: QueryData) {
    if (this.connectionEstablished) {
      this.oboeInstance.abort();
    }

    const streamingSubject = new Subject();
    this.oboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: filter,
      withCredentials: true
    }).start(data => {
      this.connectionEstablished = true;
    }).node('!.*', data => {
      streamingSubject.next(data);
    }).done(data => {
      this.connectionEstablished = false;
      this.streamingFinishedSubject.next(true);
      streamingSubject.next(null); // Emit null so the loading service can stop the loading overlay even if no variants were received
    }).fail(error => {
      this.connectionEstablished = false;
      this.streamingFinishedSubject.next(true);
      console.warn('oboejs encountered a fail event while streaming');
      streamingSubject.next(null);
    });

    return streamingSubject;
  }

  summaryStreamPost(url: string, filter: QueryData) {
    if (this.summaryConnectionEstablished) {
      console.log('Aborted');
      this.oboeInstance.abort();
    }

    const streamingSubject = new Subject();
    this.oboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: filter,
      withCredentials: true
    }).start(data => {
      this.summaryConnectionEstablished = true;
    }).node('!.*', data => {
      streamingSubject.next(data);
    }).done(data => {
      this.summaryConnectionEstablished = false;
      this.summaryStreamingFinishedSubject.next(true);
      streamingSubject.next(null); // Emit null so the loading service can stop the loading overlay even if no variants were received
    }).fail(error => {
      this.summaryConnectionEstablished = false;
      this.summaryStreamingFinishedSubject.next(true);
      console.warn('oboejs encountered a fail event while streaming');
      console.log(error);
      streamingSubject.next(null);
    });

    return streamingSubject;
  }

  getGenotypePreviewVariantsByFilter(
    filter: QueryData, genotypePreviewInfo: GenotypePreviewInfo, loadingService?: any, maxVariantsCount: number = 1001
  ): GenotypePreviewVariantsArray {
    const genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();
    const queryFilter = {...filter};
    queryFilter['maxVariantsCount'] = maxVariantsCount;

    this.streamPost(this.genotypePreviewVariantsUrl, queryFilter).subscribe(variant => {
      this.parseGenotypePreviewVariantsResponse(variant, genotypePreviewInfo, genotypePreviewVariantsArray);
      if (loadingService) {
        loadingService.setLoadingStop(); // Stop the loading overlay when at least one variant has been loaded
      }
    });

    return genotypePreviewVariantsArray;
  }

  getGeneViewVariants(filter: QueryData, loadingService?: any) {
    const summaryVariantsArray = new GeneViewSummaryVariantsArray();
    this.summaryStreamPost(this.geneViewVariants, filter).subscribe((variant: string[]) => {
      summaryVariantsArray.addSummaryRow(variant);
    });
    return summaryVariantsArray;
  }

  saveQuery(queryData: {}, page: string) {
    const options = { headers: this.headers };
    const data = {
      data: queryData,
      page: page
    };

    return this.http
      .post(this.config.baseUrl + this.saveQueryEndpoint, data, options)
      .map(response => response);
  }

  loadQuery(uuid: string) {
    const options = { headers: this.headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.loadQueryEndpoint, { uuid: uuid }, options)
      .map(response => response);
  }

  deleteQuery(uuid: string) {
    const options = { headers: this.headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.deleteQueryEndpoint, { uuid: uuid }, options)
      .map(response => response);
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
      .map(response => response);
  }

  collectUserSavedQueries() {
    const options = { withCredentials: true };
    return this.http
      .get(this.config.baseUrl + this.userCollectQueriesEndpoint, options)
      .map(response => response);
  }
}
