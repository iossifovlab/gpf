import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GenePlotComponent } from './gene-plot.component';

describe('GenePlotComponent', () => {
  let component: GenePlotComponent;
  let fixture: ComponentFixture<GenePlotComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GenePlotComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(GenePlotComponent);
    component = fixture.componentInstance;
    (component.gene as object) = {geneSymbol: 'POGZ'};
    (component['frequencyDomain'] as [number, number]) = [0, 0];
    (component.allVariantsCounts as [number, number]) = [0, 0];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
