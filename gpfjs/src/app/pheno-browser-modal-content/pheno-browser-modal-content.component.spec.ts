import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoBrowserModalContentComponent } from './pheno-browser-modal-content.component';

describe('PhenoBrowserModalContentComponent', () => {
  let component: PhenoBrowserModalContentComponent;
  let fixture: ComponentFixture<PhenoBrowserModalContentComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoBrowserModalContentComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoBrowserModalContentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
