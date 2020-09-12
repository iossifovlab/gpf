import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CommonReportsRowComponent } from './common-reports-row.component';

describe('CommonReportsRowComponent', () => {
  let component: CommonReportsRowComponent;
  let fixture: ComponentFixture<CommonReportsRowComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CommonReportsRowComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CommonReportsRowComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
