import { Component, Input } from '@angular/core';
import { LegendItem } from 'app/variant-reports/variant-reports';

@Component({
  selector: 'gpf-legend',
  templateUrl: './legend.component.html',
  styleUrls: ['./legend.component.css']
})
export class LegendComponent {

  @Input('visible') public visible: boolean = false;

  @Input('legend') public legend: Array<LegendItem> = [];

  public expanded: boolean = false;

  public expand() {
    this.expanded = !this.expanded;
  }
}
