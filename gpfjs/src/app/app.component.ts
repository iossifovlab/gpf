import { Component, HostListener, OnInit } from '@angular/core';
import { environment } from '../environments/environment';
import { BnNgIdleService } from 'bn-ng-idle';
import { UsersService } from './users/users.service';
import { switchMap } from 'rxjs/operators';
import { GeneProfilesService } from './gene-profiles-block/gene-profiles.service';
import { GeneProfilesSingleViewConfig } from './gene-profiles-single-view/gene-profiles-single-view';

@Component({
  selector: 'gpf-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  public title = 'GPF: Genotypes and Phenotypes in Families';
  public imgPathPrefix = environment.imgPathPrefix;
  public geneProfilesConfig: GeneProfilesSingleViewConfig;
  public currentRoute = '';
  private sessionTimeoutInSeconds = 7 * 24 * 60 * 60; // 1 week

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
  ) { }

  public ngOnInit(): void {
    this.bnIdle.startWatching(this.sessionTimeoutInSeconds)
      .pipe(
        switchMap(() => this.usersService.logout()),
        switchMap(() => this.usersService.getUserInfo()),
      ).subscribe();

    this.geneProfilesService.getConfig().subscribe(res => {
      this.geneProfilesConfig = res;
    });
    // First route depends on which tool the user navigates
    this.currentRoute = window.location.pathname.split('/')[1];
    // If the initial url is empty set route to home
    if (!this.currentRoute) {
      this.currentRoute = 'home';
    }
  }
}
