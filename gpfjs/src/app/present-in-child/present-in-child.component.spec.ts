import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { of } from 'rxjs';
import { PresentInChildComponent } from './present-in-child.component';
import { presentInChildReducer, setPresentInChild } from './present-in-child.state';
import { Store, StoreModule } from '@ngrx/store';

describe('PresentInChildComponent', () => {
  let component: PresentInChildComponent;
  let fixture: ComponentFixture<PresentInChildComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PresentInChildComponent],
      providers: [],
      imports: [StoreModule.forRoot({presentInChild: presentInChildReducer})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PresentInChildComponent);
    component = fixture.componentInstance;

    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2']));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore state on initialization', () => {
    component.ngOnInit();
    expect(component.selectedValues).toStrictEqual(new Set(['value1', 'value2']));
  });


  it('should update present in child', () => {
    component.selectedValues = undefined;
    // component['store'] = { dispatch() {} } as any;
    // jest.spyOn(store, 'dispatch').mockReturnValue();

    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updatePresentInChild(mockSet);

    expect(component.selectedValues).toStrictEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, setPresentInChild({presentInChild: [...mockSet]}));
  });
});
