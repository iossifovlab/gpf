import { Component, Input, Output, EventEmitter } from '@angular/core';
import { environment } from '../../environments/environment';

@Component({
  selector: 'gpf-remove-button',
  templateUrl: './remove-button.component.html',
  styleUrls: ['./remove-button.component.css'],
  standalone: false
})
export class RemoveButtonComponent {
  @Input() public field: any;
  @Output() public removeFilter: EventEmitter<any> = new EventEmitter(true);
  public imgPathPrefix = environment.imgPathPrefix;

  public remove(): void {
    this.removeFilter.emit(this.field);
  }
}
