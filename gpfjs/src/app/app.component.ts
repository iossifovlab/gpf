import { Component } from '@angular/core';
import { Dataset } from './datasets/datasets';

@Component({
  selector: 'gpf-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  selectedDataset: Dataset;
  genotypePreviewsArray: any;
  title = 'GPF: Genotypes and Phenotypes in Families';

  updateGenotypePreviewsArray(genotypePreviewsArray) {
    this.genotypePreviewsArray = genotypePreviewsArray;
  }
}
