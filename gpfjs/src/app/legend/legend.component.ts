import { Component, Input } from '@angular/core';
import { LegendItem } from 'app/variant-reports/variant-reports';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-legend',
  templateUrl: './legend.component.html',
  styleUrls: ['./legend.component.css'],
  standalone: false
})
export class LegendComponent {
  @Input() public legendItems: Array<LegendItem> = [];
  public isExpanded = false;
  public imgPathPrefix = environment.imgPathPrefix;
}
