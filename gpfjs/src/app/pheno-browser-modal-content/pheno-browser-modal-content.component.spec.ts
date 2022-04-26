import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { PhenoBrowserModalContentComponent } from './pheno-browser-modal-content.component';

describe('PhenoBrowserModalContentComponent', () => {
  let component: PhenoBrowserModalContentComponent;
  let fixture: ComponentFixture<PhenoBrowserModalContentComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoBrowserModalContentComponent],
      providers: [NgbActiveModal],
    }).compileComponents();
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
