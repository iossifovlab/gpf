import { Component, HostListener, OnInit } from '@angular/core';
import { environment } from '../environments/environment';
import { BnNgIdleService } from 'bn-ng-idle';
import { UsersService } from './users/users.service';
import { switchMap } from 'rxjs/operators';
import { GeneProfilesService } from './gene-profiles-block/gene-profiles.service';
import { GeneProfilesSingleViewConfig } from './gene-profiles-single-view/gene-profiles-single-view';
import { NgbConfig } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngrx/store';
import { selectDatasetId } from './datasets/datasets.state';
import { AuthService } from './auth.service';
import { Router } from '@angular/router';

function extractAuthParamsFromURL(): [string, string] {
  const url = new URL(window.location.href);
  const state = url.searchParams.get('state');
  const authCode = url.searchParams.get('code');
  let redirectTo: string = null;
  if (state) {
    const stateObj = JSON.parse(atob(state)) as object;
    if (stateObj['came_from']) {
      redirectTo = stateObj['came_from'] as string;
    }
  }
  return [authCode, redirectTo];
}

@Component({
    selector: 'gpf-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.css'],
    standalone: false
})
export class AppComponent implements OnInit {
  public title = 'GPF: Genotypes and Phenotypes in Families';
  public imgPathPrefix = environment.imgPathPrefix;
  public selectedDatasetId: string;
  public geneProfilesConfig: GeneProfilesSingleViewConfig;
  private sessionTimeoutInSeconds = 7 * 24 * 60 * 60; // 1 week

  /* loadedUserInfo is used to determine if the user has
     been successfully logged in. Only after a successful
     login will the application render, as the app template uses
     an *ngIf directive to test loadedUserInfo has been set. */
  public loadedUserInfo = null;

  @HostListener('window:keydown.home')
  public scrollToTop(): void {
    window.scrollTo(0, 0);
  }

  @HostListener('window:keydown.end')
  public scrollToBottom(): void {
    window.scrollTo(0, document.body.scrollHeight || document.documentElement.scrollHeight);
  }

  public constructor(
    private geneProfilesService: GeneProfilesService,
    private bnIdle: BnNgIdleService,
    private usersService: UsersService,
    private ngbConfig: NgbConfig,
    private authService: AuthService,
    private router: Router,
    protected store: Store,
  ) {
  }

  public ngOnInit(): void {
    this.ngbConfig.animation = false;

    const [authCode, redirectTo] = extractAuthParamsFromURL();

    if (authCode !== null) {
      this.authService.requestAccessToken(authCode).pipe(
        switchMap(() => this.usersService.getUserInfo()),
      ).subscribe(res => {
        this.loadedUserInfo = res;
      });
    } else {
      this.usersService.getUserInfo().subscribe(res => {
        this.loadedUserInfo = res;
      });
    }

    this.bnIdle.startWatching(this.sessionTimeoutInSeconds)
      .pipe(
        switchMap(() => this.usersService.logout())
      ).subscribe();

    this.store.select(selectDatasetId).subscribe(datasetId => {
      this.selectedDatasetId = datasetId;
    });

    this.geneProfilesService.getConfig().subscribe(res => {
      this.geneProfilesConfig = res;
    });

    if (redirectTo !== null) {
      this.router.navigate([redirectTo]);
    }
  }
}
