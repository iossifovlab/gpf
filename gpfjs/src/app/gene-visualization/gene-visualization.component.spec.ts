import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GeneVisualizationComponent } from './gene-visualization.component';

describe('GeneVisualizationComponent', () => {
  let component: GeneVisualizationComponent;
  let fixture: ComponentFixture<GeneVisualizationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GeneVisualizationComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GeneVisualizationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
