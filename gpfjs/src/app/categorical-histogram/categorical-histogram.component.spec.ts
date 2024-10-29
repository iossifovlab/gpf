import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CategoricalHistogramComponent } from './categorical-histogram.component';

describe('CategoricalHistogramComponent', () => {
  let component: CategoricalHistogramComponent;
  let fixture: ComponentFixture<CategoricalHistogramComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CategoricalHistogramComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(CategoricalHistogramComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
