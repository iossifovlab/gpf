import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { InheritancetypesComponent } from './inheritancetypes.component';

describe('InheritancetypesComponent', () => {
  let component: InheritancetypesComponent;
  let fixture: ComponentFixture<InheritancetypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ InheritancetypesComponent ]
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
});
