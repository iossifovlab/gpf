import { Component, Output, EventEmitter, Input } from '@angular/core';
import { ConfirmCancelEvent } from 'angular-confirmation-popover/lib/confirmation-popover.directive';

@Component({
    selector: 'gpf-confirm-button',
    templateUrl: './confirm-button.component.html',
    styleUrls: ['./confirm-button.component.css'],
    standalone: false
})
export class ConfirmButtonComponent {
  @Input() public hide = false;
  @Input() public message = '';
  @Input() public confirmText = 'Remove';
  @Input() public title = 'Remove';
  @Input() public iconStyle: {name: string; class: string} = {name: '', class: ''};
  @Output() public clicked = new EventEmitter(true);

  public onClick(event: ConfirmCancelEvent): void {
    this.clicked.next(event);
  }
}
