import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { Observable, Subject, Subscription } from 'rxjs';
import { environment } from 'environments/environment';
import { ConfigService } from '../config/config.service';
import { GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';
import { map, mergeMap, take, tap } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';
import { AuthService } from 'app/auth.service';
import oboe from 'oboe';
import { InstanceService } from 'app/instance.service';

type QueryFilter = Record<string, unknown>;

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

  private oboeInstance: oboe.Instance | null = null;
  private summaryOboeInstance: oboe.Instance | null = null;
  public streamingSubject = new Subject<unknown>();
  public summaryStreamingSubject = new Subject<object>();
  public streamingStartSubject = new Subject<boolean>();
  public streamingUpdateSubject = new Subject<boolean>();
  public streamingFinishedSubject = new Subject<boolean>();
  public summaryStreamingFinishedSubject = new Subject<boolean>();

  private familyVariantsSubscription: Subscription | null = null;

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

  public isStreamingActive(): boolean {
    return this.oboeInstance !== null;
  }

  public streamPost(url: string, filter: QueryFilter): Subject<unknown> {
    this.cancelStreamPost();

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
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
    }).done(() => {
      this.streamingFinishedSubject.next(true);
      // Emit null so the loading service can stop the loading overlay even if no variants were received
      this.streamingSubject.next(null);
      this.familyVariantsSubscription?.unsubscribe();
      this.familyVariantsSubscription = null;
      this.oboeInstance = null;
    }).fail(error => {
      console.warn('oboejs encountered a fail event while streaming');
      console.error(error);
      this.streamingFinishedSubject.next(true);
      this.streamingSubject.next(null);
      this.oboeInstance = null;
    });

    return this.streamingSubject;
  }

  public cancelSummaryStreamPost(): void {
    if (this.summaryOboeInstance !== null) {
      this.summaryOboeInstance.abort();
      this.summaryOboeInstance = null;
    }
  }

  public summaryStreamPost(url: string, filter: QueryFilter): Subject<object> {
    this.cancelSummaryStreamPost();

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
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
      this.summaryStreamingSubject.next(data as object);
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
    dataset: Dataset, filter: QueryFilter, maxVariantsCount: number = 1001,
    callback?: () => void,
  ): GenotypePreviewVariantsArray {
    const genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();
    const queryFilter: QueryFilter = { ...filter, maxVariantsCount: maxVariantsCount };

    this.familyVariantsSubscription = this.instanceService.getGenome().pipe(
      take(1),
      mergeMap(genome =>
        this.streamPost(this.genotypePreviewVariantsUrl, queryFilter).pipe(
          tap(variant => {
            // streamPost emits null on stream-done as a "no more variants"
            // sentinel (see streamPost.done()). Skip addPreviewVariant on
            // null — addPreviewVariant → GenotypePreview.fromJson would
            // throw on `null.length`, killing the subscription before the
            // callback runs and stranding consumers on "Loading variants..."
            // for 0-variant queries (tb-iuv Mode A root cause).
            if (variant) {
              genotypePreviewVariantsArray.addPreviewVariant(
                variant as string[],
                dataset.genotypeBrowserConfig.columnIds
              );
              // Attach the genome version to each variant to generate USCS link
              genotypePreviewVariantsArray.genotypePreviews[
                genotypePreviewVariantsArray.genotypePreviews.length - 1
              ].data.set('genome', genome);
            }
            // Always run callback (including on the null sentinel) so
            // consumers can update count displays even when the result set
            // is empty.
            if (callback !== undefined) {
              callback();
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
