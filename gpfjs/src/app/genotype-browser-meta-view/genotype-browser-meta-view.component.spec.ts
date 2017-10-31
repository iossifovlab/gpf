import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GenotypeBrowserMetaViewComponent } from './genotype-browser-meta-view.component';

describe('GenotypeBrowserMetaViewComponent', () => {
  let component: GenotypeBrowserMetaViewComponent;
  let fixture: ComponentFixture<GenotypeBrowserMetaViewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GenotypeBrowserMetaViewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypeBrowserMetaViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
