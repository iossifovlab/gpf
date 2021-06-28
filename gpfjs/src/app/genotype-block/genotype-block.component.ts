import { Component, Input } from '@angular/core';
import { Dataset } from '../datasets/datasets';

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css'],
})
export class GenotypeBlockComponent {
  @Input()
  dataset: Dataset;

  constructor() { }
}
