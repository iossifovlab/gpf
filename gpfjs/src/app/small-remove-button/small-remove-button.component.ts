import { Component, Output, EventEmitter, Input } from '@angular/core';

@Component({
  selector: 'gpf-small-remove-button',
  templateUrl: './small-remove-button.component.html',
  styleUrls: ['./small-remove-button.component.css']
})
export class SmallRemoveButtonComponent {
  @Input() hide = false;
  @Input() message = '';
  @Input() confirmText = 'Remove';
  @Input() title = 'Remove';
  @Output() clicked = new EventEmitter(true);

  onClick(event: any) {
    this.clicked.next(event);
  }
}
