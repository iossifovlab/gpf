import { NO_ERRORS_SCHEMA } from '@angular/compiler';
import { Component, ViewChild } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgxsModule } from '@ngxs/store';
import { CheckboxListComponent } from 'app/checkbox-list/checkbox-list.component';
import { of } from 'rxjs';

import { ErrorsAlertComponent } from '../errors-alert/errors-alert.component';
import { InheritancetypesComponent } from './inheritancetypes.component';
import { SetInheritanceTypes } from './inheritancetypes.state';

describe('InheritancetypesComponent', () => {
  let component: InheritancetypesComponent;
  let fixture: ComponentFixture<InheritancetypesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        ErrorsAlertComponent,
        InheritancetypesComponent,
        CheckboxListComponent
      ],
      imports: [NgxsModule.forRoot([]) ],
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(InheritancetypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should handle selected values input and/or restore state', () => {
    let dispatchSpy;

    component['store'] = {
      selectOnce(f) {
        return of({inheritanceTypes: ['value1', 'value2']});
      },
      dispatch(set) {}
    } as any;
    dispatchSpy = spyOn(component['store'], 'dispatch');
    component.ngOnChanges();
    expect(component.selectedValues).toEqual(new Set(['value1', 'value2']));
    expect(dispatchSpy).not.toHaveBeenCalled();

    component.selectedValues = new Set(['value3']);
    component['store'] = {
      selectOnce(f) {
        return of({inheritanceTypes: []});
      },
      dispatch(set) {}
    } as any;
    dispatchSpy = spyOn(component['store'], 'dispatch');
    component.ngOnChanges();
    expect(component.selectedValues).toEqual(new Set(['value3']));
    expect(dispatchSpy).toHaveBeenCalled();

  });

  it('should update variant types', () => {
    component.selectedValues = undefined;
    component['store'] = { dispatch(set) {} } as any;
    const dispatchSpy = spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updateInheritanceTypes(mockSet);

    expect(component.selectedValues).toEqual(mockSet);
    expect(dispatchSpy).toHaveBeenCalledOnceWith(new SetInheritanceTypes(mockSet));
  });
});
