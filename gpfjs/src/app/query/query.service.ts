import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
// eslint-disable-next-line no-restricted-imports
import { Observable, Subject } from 'rxjs';
const oboe = require('oboe');
import { environment } from 'environments/environment';
import { ConfigService } from '../config/config.service';
import { GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';
import { SummaryAllelesArray } from '../gene-browser/summary-variants';
import { map } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';
import { AuthService } from 'app/auth.service';

@Injectable()
export class QueryService {
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

  public constructor(
    private location: Location,
    private router: Router,
    private http: HttpClient,
    private config: ConfigService,
    private authService: AuthService
  ) { }

  public cancelStreamPost(): void {
    if (this.oboeInstance) {
      this.oboeInstance.abort();
      this.oboeInstance = null;
    }
  }

  public streamPost(url: string, filter) {
    this.cancelStreamPost();

    const headers = { 'Content-Type': 'application/json' };
    if (this.authService.getAccessToken() !== '') {
      headers['Authorization'] = `Bearer ${this.authService.getAccessToken()}`;
    }

    this.oboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: headers,
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

  public cancelSummaryStreamPost(): void {
    if (this.summaryOboeInstance) {
      this.summaryOboeInstance.abort();
      this.summaryOboeInstance = null;
    }
  }

  public summaryStreamPost(url: string, filter): Subject<unknown> {
    if (this.summaryOboeInstance) {
      this.summaryOboeInstance.abort();
      this.summaryOboeInstance = null;
    }

    const headers = { 'Content-Type': 'application/json' };
    if (this.authService.getAccessToken() !== '') {
      headers['Authorization'] = `Bearer ${this.authService.getAccessToken()}`;
    }

    this.summaryOboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: headers,
      body: filter,
      withCredentials: true
    }).node('!.*', data => {
      this.summaryStreamingSubject.next(data);
    }).done(() => {
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

  public getGenotypePreviewVariantsByFilter(
    dataset: Dataset, filter, maxVariantsCount: number = 1001,
    callback?: () => void,
  ): GenotypePreviewVariantsArray {
    const genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();
    const queryFilter = { ...filter };
    queryFilter['maxVariantsCount'] = maxVariantsCount;

    this.streamPost(this.genotypePreviewVariantsUrl, queryFilter).subscribe(variant => {
      genotypePreviewVariantsArray.addPreviewVariant(
        <Array<string>> variant,
        dataset.genotypeBrowserConfig.columnIds
      );

      if (callback !== undefined) {
        callback();
      }

      if (variant) {
        // Attach the genome version to each variant
        // This is done so that the table can construct the correct UCSC link for the variant
        genotypePreviewVariantsArray.genotypePreviews[
          genotypePreviewVariantsArray.genotypePreviews.length - 1
        ].data.set('genome', dataset.genome);
      }
    });

    return genotypePreviewVariantsArray;
  }

  public getSummaryVariants(filter): SummaryAllelesArray {
    const summaryVariantsArray = new SummaryAllelesArray();
    this.summaryStreamPost(this.geneViewVariants, filter).subscribe((variant: string[]) => {
      summaryVariantsArray.addSummaryRow(variant);
    });
    return summaryVariantsArray;
  }

  public saveQuery(queryData: {}, page: string): Observable<object> {
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

  public loadQuery(uuid: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.loadQueryEndpoint, { uuid: uuid }, options)
      .pipe(map(response => response));
  }

  public deleteQuery(uuid: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };

    return this.http
      .post(this.config.baseUrl + this.deleteQueryEndpoint, { uuid: uuid }, options)
      .pipe(map(response => response));
  }

  public getLoadUrl(uuid: string): string {
    let pathname = this.router.createUrlTree(['load-query', uuid]).toString();
    pathname = this.location.prepareExternalUrl(pathname);

    return window.location.origin + pathname;
  }

  public getLoadUrlFromResponse(response: {}): string {
    return this.getLoadUrl(response['uuid']);
  }

  public saveUserQuery(uuid: string, query_name: string, query_description: string): Observable<object> {
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

  public collectUserSavedQueries(): Observable<object> {
    const options = { withCredentials: true };
    return this.http
      .get(this.config.baseUrl + this.userCollectQueriesEndpoint, options)
      .pipe(map(response => response));
  }
}
