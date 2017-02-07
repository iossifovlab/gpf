import { Component } from '@angular/core';

// import './rxjs-operators';

@Component({
  selector: 'gpf-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  genotypePreviewsArray: any;
  title = 'GPF: Genotypes and Phenotypes in Families';

  updateGenotypePreviewsArray(genotypePreviewsArray) {
    this.genotypePreviewsArray = genotypePreviewsArray;
  }
}
