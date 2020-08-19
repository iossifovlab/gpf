import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VariantFrequencyViewComponent } from './variant-frequency-view.component';

describe('VariantFrequencyViewComponent', () => {
  let component: VariantFrequencyViewComponent;
  let fixture: ComponentFixture<VariantFrequencyViewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VariantFrequencyViewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VariantFrequencyViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
