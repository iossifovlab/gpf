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

@Component({
  selector: 'gpf-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  public title = 'GPF: Genotypes and Phenotypes in Families';
  public imgPathPrefix = environment.imgPathPrefix;
  public selectedDatasetId: string;
  public geneProfilesConfig: GeneProfilesSingleViewConfig;
  private sessionTimeoutInSeconds = 7 * 24 * 60 * 60; // 1 week

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

    const url = new URL(window.location.href);
    let state = url.searchParams.get('state');
    let authCode = url.searchParams.get('code');
    let redirectTo = null;
    if (state) {
      state = JSON.parse(atob(state));
      if (state['came_from']) {
        redirectTo = [state['came_from']];
      }
    }

    if (authCode !== null) {
      this.authService.requestAccessToken(authCode).pipe(
        switchMap(() => this.usersService.getUserInfo()),
      ).subscribe(res => {
        this.loadedUserInfo = res;
      })
    } else {
      this.usersService.getUserInfo().subscribe(res => {
        this.loadedUserInfo = res;
      })
    }

    this.bnIdle.startWatching(this.sessionTimeoutInSeconds)
      .pipe(
        switchMap(() => this.usersService.logout()),
        switchMap(() => this.usersService.getUserInfo()),
      ).subscribe();

    this.store.select(selectDatasetId).subscribe(datasetId => {
      this.selectedDatasetId = datasetId;
    });

    this.geneProfilesService.getConfig().subscribe(res => {
      this.geneProfilesConfig = res;
    });

    if (redirectTo !== null) {
      this.router.navigate(redirectTo);
    }
  }
}
