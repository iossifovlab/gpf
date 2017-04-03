import { Component, OnInit, Input } from '@angular/core';
import { GenotypeBrowser } from '../datasets/datasets';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css']
})
export class FamilyFiltersBlockComponent implements OnInit {
  @Input() genotypeBrowserConfig: GenotypeBrowser;
  @Input() datasetId: string;

  constructor() { }

  ngOnInit() {
  }

}
