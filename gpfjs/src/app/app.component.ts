import { Component } from '@angular/core';
import { Dataset } from './datasets/datasets';

@Component({
  selector: 'gpf-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'GPF: Genotypes and Phenotypes in Families';
}
