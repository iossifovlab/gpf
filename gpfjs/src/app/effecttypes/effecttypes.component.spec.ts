/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { EffecttypesComponent, EffecttypesColumnComponent } from './effecttypes.component';

import { gpfReducer } from '../store/gpf-store';
import { StoreModule } from '@ngrx/store';


describe('EffecttypesComponent', () => {
  let component: EffecttypesComponent;
  let fixture: ComponentFixture<EffecttypesComponent>;

  beforeEach(async(() => {
    const storeSpy = jasmine.createSpyObj('Store', ['dispatch', 'subscribe', 'select', 'let']);
    TestBed.configureTestingModule({
      declarations: [
        EffecttypesComponent,
        EffecttypesColumnComponent,
      ],
      imports: [
        StoreModule.provideStore(gpfReducer),
      ],
      providers: [
      ]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EffecttypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
