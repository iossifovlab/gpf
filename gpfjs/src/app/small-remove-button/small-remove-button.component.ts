import { Component, Output, EventEmitter, Input } from '@angular/core';

@Component({
  selector: 'gpf-small-remove-button',
  templateUrl: './small-remove-button.component.html',
  styleUrls: ['./small-remove-button.component.css']
})
export class SmallRemoveButtonComponent {
  @Input() public hide = false;
  @Input() public message = '';
  @Input() public confirmText = 'Remove';
  @Input() public title = 'Remove';
  @Output() public clicked = new EventEmitter(true);

  public onClick(event: any): void {
    this.clicked.next(event);
  }
}
