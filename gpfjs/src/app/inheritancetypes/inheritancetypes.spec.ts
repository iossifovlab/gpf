import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { InheritanceTypes } from './inheritancetypes';

describe('InheritanceTypes ', () => {
  it('should create and set available and selected sets', () => {
    let inheritanceTypes = new InheritanceTypes(['mendelian', 'denovo'], ['denovo']);
    expect(inheritanceTypes).toBeTruthy();
    expect(inheritanceTypes.available).toEqual(new Set(['mendelian', 'denovo']));
    expect(inheritanceTypes.selected).toEqual(new Set(['denovo']));
  });
});
