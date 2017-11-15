import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GenotypePreviewFieldComponent } from './genotype-preview-field.component';

describe('GenotypePreviewFieldComponent', () => {
  let component: GenotypePreviewFieldComponent;
  let fixture: ComponentFixture<GenotypePreviewFieldComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GenotypePreviewFieldComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypePreviewFieldComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
