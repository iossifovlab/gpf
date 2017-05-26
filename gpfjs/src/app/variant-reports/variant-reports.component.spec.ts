import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VariantReportsComponent } from './variant-reports.component';

describe('VariantReportsComponent', () => {
  let component: VariantReportsComponent;
  let fixture: ComponentFixture<VariantReportsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VariantReportsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VariantReportsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
