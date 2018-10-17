import { Component, Input, Output } from '@angular/core';
import { EventEmitter } from '@angular/core';

import { environment } from '../../environments/environment';

@Component({
  selector: 'gpf-remove-button',
  templateUrl: './remove-button.component.html',
  styleUrls: ['./remove-button.component.css']
})
export class RemoveButtonComponent {
  @Input() field: any;
  @Output() removeFilter: EventEmitter<any> = new EventEmitter(true);

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }

  remove() {
    this.removeFilter.emit(this.field);
  }

  constructor() { }

}
