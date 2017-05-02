import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoBrowserTableComponent } from './pheno-browser-table.component';

describe('PhenoBrowserTableComponent', () => {
  let component: PhenoBrowserTableComponent;
  let fixture: ComponentFixture<PhenoBrowserTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoBrowserTableComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoBrowserTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
