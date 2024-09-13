import { Component, HostListener, OnInit } from '@angular/core';
import { environment } from '../environments/environment';
import { BnNgIdleService } from 'bn-ng-idle';
import { UsersService } from './users/users.service';
import { switchMap, take } from 'rxjs/operators';
import { GeneProfilesService } from './gene-profiles-block/gene-profiles.service';
import { GeneProfilesSingleViewConfig } from './gene-profiles-single-view/gene-profiles-single-view';
import { NgbConfig } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngrx/store';
import { selectDatasetId } from './datasets/datasets.state';

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
    protected store: Store,
  ) {
    ngbConfig.animation = false;
  }

  public ngOnInit(): void {
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
  }
}
