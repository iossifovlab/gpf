import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HelperModalComponent } from './helper-modal.component';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { PopupComponent } from 'app/popup/popup.component';

describe('HelperModalComponent', () => {
  let component: HelperModalComponent;
  let fixture: ComponentFixture<HelperModalComponent>;
  let modalService: NgbModal;
  let modalRef: NgbModalRef;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [HelperModalComponent]
    }).compileComponents();
    modalService = TestBed.inject(NgbModal);
    modalRef = modalService.open(PopupComponent);

    fixture = TestBed.createComponent(HelperModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show help', () => {
    component.modalContent = 'modalContentTest';
    jest.spyOn(modalService, 'open').mockReturnValue(modalRef);
    component.showHelp();
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg',
      centered: true
    });
    expect((modalRef.componentInstance as PopupComponent).data).toBe('modalContentTest');

    modalRef.close();
  });
});
