import { Component, Input } from '@angular/core';

@Component({
  selector: 'gpf-nothing-found-row',
  templateUrl: './nothing-found-row.component.html',
  styleUrls: ['./nothing-found-row.component.css'],
})
export class GpfTableNothingFoundRowComponent {
  @Input() public width: string;
}
