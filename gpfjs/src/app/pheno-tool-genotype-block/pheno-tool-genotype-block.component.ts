import { Component, Input } from '@angular/core';

@Component({
  selector: 'gpf-pheno-tool-genotype-block',
  templateUrl: './pheno-tool-genotype-block.component.html',
  styleUrls: ['./pheno-tool-genotype-block.component.css'],
})
export class PhenoToolGenotypeBlockComponent {
  @Input() public variantTypes: Set<string> = new Set();
}
