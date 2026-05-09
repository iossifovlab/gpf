import { Component, Input } from '@angular/core';

@Component({
  selector: 'gpf-errors-alert',
  templateUrl: './errors-alert.component.html',
  standalone: false
})
export class ErrorsAlertComponent {
  @Input() public errors: Array<string>;
}
