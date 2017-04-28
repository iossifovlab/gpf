import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoBrowserComponent } from './pheno-browser.component';

describe('PhenoBrowserComponent', () => {
  let component: PhenoBrowserComponent;
  let fixture: ComponentFixture<PhenoBrowserComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoBrowserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoBrowserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
