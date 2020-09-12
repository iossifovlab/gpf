import { Directive, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[pedigreeHost]'
})
export class CommonReportsPedigreeCellDirective {

  constructor(public viewContainerRef: ViewContainerRef) { }

}
