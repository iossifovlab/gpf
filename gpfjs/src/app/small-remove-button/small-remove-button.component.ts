import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';

@Component({
  selector: 'gpf-small-remove-button',
  templateUrl: './small-remove-button.component.html',
  styleUrls: ['./small-remove-button.component.css']
})
export class SmallRemoveButtonComponent implements OnInit {

  @Output()
  clicked = new EventEmitter(true);

  @Input()
  hide = false;

  @Input()
  message = '';

  @Input()
  confirmText = 'Remove';

  @Input()
  title = 'Remove';

  constructor() { }

  ngOnInit() {
  }

  onClick(event: any) {
    this.clicked.next(event);
  }

}
