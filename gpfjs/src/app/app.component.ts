import { Component, trigger, transition, style, animate } from '@angular/core';
import { Dataset } from './datasets/datasets';
import { environment } from '../environments/environment';

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
