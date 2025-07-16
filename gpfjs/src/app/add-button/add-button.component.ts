import { Component, Output, EventEmitter } from '@angular/core';
import { environment } from '../../environments/environment';

@Component({
    selector: 'gpf-add-button',
    templateUrl: './add-button.component.html',
    styleUrls: ['./add-button.component.css'],
    standalone: false
})
export class AddButtonComponent {
  @Output() public addFilter: EventEmitter<void> = new EventEmitter<void>(true);
  public imgPathPrefix = environment.imgPathPrefix;

  public add(): void {
    this.addFilter.emit(null);
  }
}
