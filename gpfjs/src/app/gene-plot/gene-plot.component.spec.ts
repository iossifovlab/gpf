import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GenePlotComponent } from './gene-plot.component';

describe('GenePlotComponent', () => {
  let component: GenePlotComponent;
  let fixture: ComponentFixture<GenePlotComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ GenePlotComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GenePlotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
