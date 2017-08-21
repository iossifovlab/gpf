import { Component, Input } from '@angular/core';
import { GenotypeBrowser } from '../datasets/datasets';


@Component({
  selector: 'gpf-missense-scores-block',
  templateUrl: './missense-scores-block.component.html',
  styleUrls: ['./missense-scores-block.component.css'],
})
export class MissenseScoresBlockComponent {
  @Input() genotypeBrowserConfig: GenotypeBrowser;
}
