import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NonPdpPedigreesComponent } from './non-pdp-pedigrees.component';

describe('NonPdpPedigreesComponent', () => {
  let component: NonPdpPedigreesComponent;
  let fixture: ComponentFixture<NonPdpPedigreesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NonPdpPedigreesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NonPdpPedigreesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
