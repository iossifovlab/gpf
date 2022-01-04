import { Component } from '@angular/core';
import { configMock } from './agp-table';

@Component({
  selector: 'gpf-agp-table',
  templateUrl: './agp-table.component.html',
  styleUrls: ['./agp-table.component.css']
})
export class AgpTableComponent {
  public config = configMock;
}
