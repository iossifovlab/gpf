import { Component, HostListener } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { environment } from '../environments/environment';
import { AutismGeneProfilesService } from './autism-gene-profiles-block/autism-gene-profiles.service';
import { BnNgIdleService } from 'bn-ng-idle';
import { UsersService } from './users/users.service';
import { AgpConfig } from './autism-gene-profiles-table/autism-gene-profile-table';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'gpf-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  animations: [
    trigger(
      'fromLeft',
      [
        transition(
          ':enter', [
            style({transform: 'translateX(-100%)'}),
            animate('250ms ease-in-out', style({transform: 'translateX(0)'}))
          ]
        ),
        transition(
          ':leave', [
            style({transform: 'translateX(0)'}),
            animate('250ms ease-in-out', style({transform: 'translateX(-100%)'})),
          ]
        )
      ]
    ),
    trigger(
      'fadeInOut',
      [
        transition(
          ':enter', [
            style({opacity: 0}),
            animate('250ms ease-in-out', style({opacity: 1}))
          ]
        ),
        transition(
          ':leave', [
            style({opacity: 1}),
            animate('250ms ease-in-out', style({opacity: 0})),
          ]
        )
      ]
    )
  ]
})
export class AppComponent {
  showSidenav = false;
  title = 'GPF: Genotypes and Phenotypes in Families';
  agpConfig: AgpConfig;
  private sessionTimeoutInSeconds = 7 * 24 * 60 * 60; // 1 week

  @HostListener('window:scroll')
  onWindowScroll() {
    this.hideSidenav();
  }

  @HostListener('document:keydown.escape')
  onEscapeButtonPress() {
    this.hideSidenav();
  }

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private bnIdle: BnNgIdleService,
    private usersService: UsersService,
  ) { }

  ngOnInit(): void {
    this.bnIdle.startWatching(this.sessionTimeoutInSeconds)
      .pipe(
        switchMap(() => {
          return this.usersService.logout();
        }),
        switchMap(() => {
          return this.usersService.getUserInfo();
        }),
      ).subscribe();

    this.autismGeneProfilesService.getConfig().subscribe(res => {
      this.agpConfig = res;
    });
  }

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }

  hideSidenav() {
    this.showSidenav = false;
  }

  toggleSidenav() {
    this.showSidenav = !this.showSidenav;
  }
}
