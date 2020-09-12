import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CommonReportsPedigreeCellComponent } from './common-reports-pedigree-cell.component';

describe('CommonReportsPedigreeCellComponent', () => {
  let component: CommonReportsPedigreeCellComponent;
  let fixture: ComponentFixture<CommonReportsPedigreeCellComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CommonReportsPedigreeCellComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CommonReportsPedigreeCellComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
