import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgxsModule } from '@ngxs/store';
// eslint-disable-next-line no-restricted-imports
import { of } from 'rxjs';

import { PresentInChildComponent } from './present-in-child.component';
import { SetPresentInChildValues } from './present-in-child.state';

describe('PresentInChildComponent', () => {
  let component: PresentInChildComponent;
  let fixture: ComponentFixture<PresentInChildComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ PresentInChildComponent ],
      providers: [],
      imports: [NgxsModule.forRoot([])],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PresentInChildComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce() {
        return of({presentInChild: ['value1', 'value2']});
      },
      dispatch() {}
    } as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore state on initialization', () => {
    component.ngOnInit();
    expect(component.selectedValues).toEqual(new Set(['value1', 'value2']));
  });


  it('should update present in child', () => {
    component.selectedValues = undefined;
    component['store'] = { dispatch(set) {} } as any;
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updatePresentInChild(mockSet);

    expect(component.selectedValues).toEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, new SetPresentInChildValues(mockSet));
  });
});
