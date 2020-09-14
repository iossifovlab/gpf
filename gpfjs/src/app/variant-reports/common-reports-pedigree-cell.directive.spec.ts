import { CommonReportsPedigreeCellDirective } from './common-reports-pedigree-cell.directive';
import { ViewContainerRef } from '@angular/core';

describe('CommonReportsPedigreeCellDirective', () => {
  it('should create an instance', () => {
    let vcr: ViewContainerRef;
    const directive = new CommonReportsPedigreeCellDirective(vcr);
    expect(directive).toBeTruthy();
  });
});
