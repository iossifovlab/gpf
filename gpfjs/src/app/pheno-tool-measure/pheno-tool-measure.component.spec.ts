import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoToolMeasureComponent } from './pheno-tool-measure.component';

describe('PhenoToolMeasureComponent', () => {
  let component: PhenoToolMeasureComponent;
  let fixture: ComponentFixture<PhenoToolMeasureComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoToolMeasureComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolMeasureComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
