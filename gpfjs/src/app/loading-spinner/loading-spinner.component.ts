import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'gpf-loading-spinner',
  templateUrl: './loading-spinner.component.html',
  styleUrls: ['./loading-spinner.component.css']
})
export class LoadingSpinnerComponent implements OnInit {

  @Input() loadingFinished: boolean;
  @Input() count: string;
  @Input() displayText: string = null;

  constructor() { }

  ngOnInit(): void {}

  getDisplayText(): string {
    if(this.displayText) {
      return this.displayText;
    }
    return "Loading..."
  }

}
