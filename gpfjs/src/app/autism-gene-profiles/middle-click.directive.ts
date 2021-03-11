import { Directive, EventEmitter, HostListener, Output } from '@angular/core';

@Directive({
  selector: '[middleclick]'
})
export class MiddleClickDirective {
  @Output('middleclick') middleClick = new EventEmitter();

  constructor() {}

  @HostListener('mouseup', ['$event'])
  middleclickEvent(event) {
    if (event.which === 2) {
      this.middleClick.emit(event);
    }
  }
}
