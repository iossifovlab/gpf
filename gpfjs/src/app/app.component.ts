import { Component } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { environment } from '../environments/environment';
import { AutismGeneProfilesService } from './autism-gene-profiles-block/autism-gene-profiles.service';

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
  private autismGeneProfilesConfig;

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.autismGeneProfilesService.getConfig().subscribe(res => {
      this.autismGeneProfilesConfig = res;
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
