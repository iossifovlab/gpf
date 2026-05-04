import { Component, Input } from '@angular/core';

@Component({
  selector: 'gpf-loading-spinner',
  templateUrl: './loading-spinner.component.html',
  styleUrls: ['./loading-spinner.component.css'],
  standalone: false
})
export class LoadingSpinnerComponent {
  @Input() public loadingFinished: boolean;
  @Input() public verboseMode = false;
  @Input() public count: string;
}
