import { Component } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider'
import { Observable } from 'rxjs';
import 'rxjs/add/operator/zip';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
})
export class GenotypeBrowserComponent extends QueryStateCollector {
  genotypePreviewsArray: any;

  printState() {
    let state = this.collectState();
    Observable.zip(...state,
    ).subscribe(
      state => {
        console.log(Object.assign({}, ...state))
      },
      error => null
    )
  }
}
