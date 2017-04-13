import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'gpf-pheno-tool-measure',
  templateUrl: './pheno-tool-measure.component.html',
  styleUrls: ['./pheno-tool-measure.component.css']
})
export class PhenoToolMeasureComponent implements OnInit {
  @Input() datasetId: string;

  constructor() { }

  ngOnInit() {
  }

}
