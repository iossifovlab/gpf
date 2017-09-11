import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GenotypePreviewChromosomesComponent } from './genotype-preview-chromosomes.component';

describe('GenotypePreviewChromosomesComponent', () => {
  let component: GenotypePreviewChromosomesComponent;
  let fixture: ComponentFixture<GenotypePreviewChromosomesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GenotypePreviewChromosomesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypePreviewChromosomesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
