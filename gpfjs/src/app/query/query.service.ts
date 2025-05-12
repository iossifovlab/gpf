import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { Observable, Subject } from 'rxjs';
import { environment } from 'environments/environment';
import { ConfigService } from '../config/config.service';
import { GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';
import { map, mergeMap, take, tap } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';
import { AuthService } from 'app/auth.service';
import oboe from 'oboe';
import { InstanceService } from 'app/instance.service';

@Injectable()
export class QueryService {
  private readonly genotypePreviewVariantsUrl = 'genotype_browser/query';
  private readonly geneViewVariantsUrl = 'gene_view/query_summary_variants';
  private readonly saveQueryEndpoint = 'query_state/save';
  private readonly loadQueryEndpoint = 'query_state/load';
  private readonly deleteQueryEndpoint = 'query_state/delete';
  private readonly userSaveQueryEndpoint = 'user_queries/save';
  private readonly userCollectQueriesEndpoint = 'user_queries/collect';

  // eslint-disable-next-line @typescript-eslint/naming-convention
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  private oboeInstance = null;
  private summaryOboeInstance = null;
  public streamingSubject = new Subject();
  public summaryStreamingSubject = new Subject<object>();
  public streamingStartSubject = new Subject();
  public streamingUpdateSubject = new Subject();
  public streamingFinishedSubject = new Subject();
  public summaryStreamingFinishedSubject = new Subject();

  private familyVariantsSubscription = null;

  public constructor(
    private location: Location,
    private router: Router,
    private http: HttpClient,
    private config: ConfigService,
    private authService: AuthService,
    private instanceService: InstanceService,
  ) { }

  public cancelStreamPost(): void {
    if (this.oboeInstance !== null) {
      this.oboeInstance.abort();
      this.oboeInstance = null;
    }
  }

  public streamPost(url: string, filter) {
    this.cancelStreamPost();

    const headers = { 'Content-Type': 'application/json' };
    if (this.authService.accessToken !== '') {
      headers['Authorization'] = `Bearer ${this.authService.accessToken}`;
    }
    this.streamingStartSubject.next(true);

    this.oboeInstance = oboe({
      url: `${environment.apiPath}${url}`,
      method: 'POST',
      headers: headers,
      body: filter,
      withCredentials: true
    }).node('!.*', data => {
      this.streamingUpdateSubject.next(true);
      this.streamingSubject.next(data);
    }).done(data => {
      this.streamingFinishedSubject.next(true);
      // Emit null so the loading service can stop the loading overlay even if no variants were received
      this.streamingSubject.next(null);
      this.familyVariantsSubscription.unsubscribe();
      this.familyVariantsSubscription = null;
    }).fail(error => {
      console.warn('oboejs encountered a fail event while streaming');
      console.error(error);
      this.streamingFinishedSubject.next(true);
      this.streamingSubject.next(null);
    });

    return this.streamingSubject;
  }

  public cancelSummaryStreamPost(): void {
    if (this.summaryOboeInstance !== null) {
      this.summaryOboeInstance.abort();
      this.summaryOboeInstance = null;
    }
  }

  public summaryStreamPost(url: string, filter): Subject<object> {
    this.cancelSummaryStreamPost();

    const headers = { 'Content-Type': 'application/json' };
    if (this.authService.accessToken !== '') {
      headers['Authorization'] = `Bearer ${this.authService.accessToken}`;
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

    this.familyVariantsSubscription = this.instanceService.getGenome().pipe(
      take(1),
      mergeMap(genome =>
        this.streamPost(this.genotypePreviewVariantsUrl, queryFilter).pipe(
          tap(variant => {
            genotypePreviewVariantsArray.addPreviewVariant(
              <Array<string>>variant,
              dataset.genotypeBrowserConfig.columnIds
            );
            if (callback !== undefined) {
              callback();
            }
            if (variant) {
              // Attach the genome version to each variant to generate USCS link
              genotypePreviewVariantsArray.genotypePreviews[
                genotypePreviewVariantsArray.genotypePreviews.length - 1
              ].data.set('genome', genome);
            }
          })
        )
      )
    ).subscribe();
    return genotypePreviewVariantsArray;
  }

  public getSummaryVariants(filter: object): Observable<object> {
    return this.http.post(this.config.baseUrl + this.geneViewVariantsUrl, filter);
  }

  public saveQuery(
    queryData: object,
    page: string,
    origin: 'saved' | 'user' | 'system',
  ): Observable<object> {
    const options = { headers: this.headers };

    queryData = {...queryData};
    delete queryData['errorsState'];

    const data = {
      data: queryData,
      page: page,
      origin: origin,
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

  public getLoadUrl(uuid: string, preview: boolean = false): string {
    const urlTree = this.router.createUrlTree(['load-query', uuid]);
    if (preview) {
      urlTree.queryParams = { preview: true };
    }
    const pathname = this.location.prepareExternalUrl(urlTree.toString());
    return window.location.origin + pathname;
  }

  public saveUserQuery(uuid: string, query_name: string, query_description: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };

    const data = {
      // eslint-disable-next-line @typescript-eslint/naming-convention
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
