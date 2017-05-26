import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CommonReportsComponent } from './common-reports.component';

describe('CommonReportsComponent', () => {
  let component: CommonReportsComponent;
  let fixture: ComponentFixture<CommonReportsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CommonReportsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CommonReportsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
