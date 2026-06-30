import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, OnDestroy, inject } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
import { Observable, of } from 'rxjs';
import { map, take } from 'rxjs/operators';
import { Store } from '@ngrx/store';
import { UsersService } from 'app/users/users.service';
import { GeneProfiles, selectGeneProfiles } from './gene-profiles-table.state';

@Injectable({
  providedIn: 'root'
})
export class GeneProfilesTableService implements OnDestroy {
  private http = inject(HttpClient);
  private config = inject(ConfigService);
  private store = inject(Store);
  private user = inject(UsersService);

  private readonly genesUrl = 'gene_profiles/table/rows';
  private readonly geneSymbolsUrl = 'gene_profiles/table/gene_symbols/';
  private readonly usersUrl = 'users/user_gp_state';
  private saveStateDebouncer: ReturnType<typeof setTimeout> = null;

  public constructor() {
    window.addEventListener('pagehide', this.flushPendingSaveOnUnload);
  }

  public ngOnDestroy(): void {
    window.removeEventListener('pagehide', this.flushPendingSaveOnUnload);
  }

  public getUserGeneProfilesState(): Observable<GeneProfiles> {
    if (!this.user.cachedUserInfo()?.loggedIn) {
      return of(null);
    }
    return this.http.get<GeneProfiles>(this.config.baseUrl + this.usersUrl, { withCredentials: true });
  }

  public saveUserGeneProfilesState(): void {
    if (!this.user.cachedUserInfo()?.loggedIn) {
      return;
    }

    if (this.saveStateDebouncer !== null) {
      clearTimeout(this.saveStateDebouncer);
    }
    this.saveStateDebouncer = setTimeout(() => {
      this.store.select(selectGeneProfiles).pipe(take(1))
        .subscribe(geneProfilesState => {
          this.http.post(this.config.baseUrl + this.usersUrl, geneProfilesState, { withCredentials: true }).subscribe();
          this.saveStateDebouncer = null;
        });
    }, 1000);
  }

  // The trailing-edge debounce in saveUserGeneProfilesState would otherwise
  // drop a state mutation made within ~1s of an unload (logout, refresh,
  // tab close, external nav). sendBeacon is the only reliable POST that
  // survives the unload.
  private readonly flushPendingSaveOnUnload = (): void => {
    if (this.saveStateDebouncer === null) {
      return;
    }
    clearTimeout(this.saveStateDebouncer);
    this.saveStateDebouncer = null;
    if (!this.user.cachedUserInfo()?.loggedIn) {
      return;
    }
    this.store.select(selectGeneProfiles).pipe(take(1)).subscribe(geneProfilesState => {
      const body = new Blob(
        [JSON.stringify(geneProfilesState)],
        { type: 'application/json' },
      );
      navigator.sendBeacon(this.config.baseUrl + this.usersUrl, body);
    });
  };

  public getGenes(page: number, searchString?: string, sortBy?: string, order?: string): Observable<any[]> {
    let url = this.config.baseUrl + this.genesUrl;
    let params = new HttpParams().set('page', page.toString());

    if (searchString) {
      params = params.append('symbol', searchString);
    }

    if (sortBy) {
      params = params.append('sortBy', sortBy);

      if (order) {
        params = params.append('order', order);
      }
    }

    url += `?${ params.toString() }`;

    return this.http.get(url).pipe(
      map(res => (res as Array<any>))
    );
  }

  public getGeneSymbols(page: number, searchString?: string): Observable<string[]> {
    let url = this.config.baseUrl + this.geneSymbolsUrl;
    let params = new HttpParams().set('page', page.toString());

    if (searchString) {
      params = params.append('symbol', searchString);
    }

    url += `?${ params.toString() }`;

    return this.http.get(url).pipe(
      map(res => (res as Array<string>))
    );
  }
}
