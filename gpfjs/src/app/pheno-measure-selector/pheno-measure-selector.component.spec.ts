import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoMeasureSelectorComponent } from './pheno-measure-selector.component';

describe('PhenoMeasureSelectorComponent', () => {
  let component: PhenoMeasureSelectorComponent;
  let fixture: ComponentFixture<PhenoMeasureSelectorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoMeasureSelectorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoMeasureSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
