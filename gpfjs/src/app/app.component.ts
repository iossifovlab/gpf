import { Component, trigger, transition, style, animate } from '@angular/core';
import { Dataset } from './datasets/datasets';
import { environment } from '../environments/environment';

@Component({
  selector: 'gpf-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  animations: [
    trigger(
      'showHide',
      [
        transition(
          ':enter', [
            style({transform: 'translateX(-100%)'}),
            animate('500ms ease-in-out', style({transform: 'translateX(0)'}))
          ]
        ),
        transition(
          ':leave', [
            style({transform: 'translateX(0)'}),
            animate('500ms ease-in-out', style({transform: 'translateX(-100%)'})),
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
}
