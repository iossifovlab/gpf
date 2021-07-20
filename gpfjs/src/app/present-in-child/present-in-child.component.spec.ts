import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgxsModule } from '@ngxs/store';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';

import { PresentInChildComponent } from './present-in-child.component';
import { SetPresentInChildValues } from './present-in-child.state';

describe('PresentInChildComponent', () => {
  let component: PresentInChildComponent;
  let fixture: ComponentFixture<PresentInChildComponent>;

  beforeEach(async(() => {
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
      selectOnce(f) {
        return of({presentInChild: ['value1', 'value2']});
      },
      dispatch(set) {}
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
    const dispatchSpy = spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updatePresentInChild(mockSet);

    expect(component.selectedValues).toEqual(mockSet);
    expect(dispatchSpy).toHaveBeenCalledOnceWith(new SetPresentInChildValues(mockSet));
  });
});
