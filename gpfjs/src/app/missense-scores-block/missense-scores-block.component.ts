import { Component, Input } from '@angular/core';
import { Dataset } from '../datasets/datasets';


@Component({
  selector: 'gpf-missense-scores-block',
  templateUrl: './missense-scores-block.component.html',
  styleUrls: ['./missense-scores-block.component.css'],
})
export class MissenseScoresBlockComponent {
  @Input() datasetConfig: Dataset;
}
