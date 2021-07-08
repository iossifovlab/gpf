import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-pheno-tool-genotype-block',
  templateUrl: './pheno-tool-genotype-block.component.html',
  styleUrls: ['./pheno-tool-genotype-block.component.css'],
})
export class PhenoToolGenotypeBlockComponent implements OnInit {

  @Input()
  variantTypes: Set<string> = new Set([]);

  constructor() { }

  ngOnInit() {
  }

}
