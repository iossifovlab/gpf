import { Component, Output } from '@angular/core';
import { EventEmitter } from '@angular/core';

import { environment } from '../../environments/environment';

@Component({
  selector: 'gpf-add-button',
  templateUrl: './add-button.component.html',
  styleUrls: ['./add-button.component.css']
})
export class AddButtonComponent {
  @Output() addFilter: EventEmitter<any> = new EventEmitter(true);

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }

  add() {
    this.addFilter.emit(null);
  }

  constructor() { }

}
