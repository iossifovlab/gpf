import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GenotypeBrowserSingleViewComponent } from './genotype-browser-single-view.component';

describe('GenotypeBrowserSingleViewComponent', () => {
  let component: GenotypeBrowserSingleViewComponent;
  let fixture: ComponentFixture<GenotypeBrowserSingleViewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GenotypeBrowserSingleViewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypeBrowserSingleViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
