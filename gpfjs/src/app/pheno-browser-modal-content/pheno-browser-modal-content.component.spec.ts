import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoBrowserModalComponent } from './pheno-browser-modal.component';

describe('PhenoBrowserModalComponent', () => {
  let component: PhenoBrowserModalComponent;
  let fixture: ComponentFixture<PhenoBrowserModalComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoBrowserModalComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoBrowserModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
