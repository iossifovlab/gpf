import { Component } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
})
export class GenotypeBrowserComponent extends QueryStateCollector {
  genotypePreviewsArray: any;
}
