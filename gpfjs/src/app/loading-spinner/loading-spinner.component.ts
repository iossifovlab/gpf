import { Component, Input } from '@angular/core';

@Component({
  selector: 'gpf-loading-spinner',
  templateUrl: './loading-spinner.component.html',
  styleUrls: ['./loading-spinner.component.css']
})
export class LoadingSpinnerComponent {
  @Input() public loadingFinished: boolean;
  @Input() public count: string;
  @Input() public displayText: string = null;

  public getDisplayText(): string {
    if (this.displayText) {
      return this.displayText;
    }
    return 'Loading...';
  }
}
