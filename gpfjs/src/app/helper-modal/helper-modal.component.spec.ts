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

  it('should show help content made from markdown', () => {
    component.modalContent = '<markdown><markdown/>';
    component.isMarkdown = true;
    fixture.detectChanges();
    jest.spyOn(modalService, 'open').mockReturnValue(modalRef);
    component.showHelp();
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg',
      centered: true
    });
    expect((modalRef.componentInstance as PopupComponent).data).toBe('<markdown><markdown/>');

    modalRef.close();
  });

  it('should not show invalid help content', () => {
    component.modalContent = '<div><div/>';
    component.isMarkdown = false;
    fixture.detectChanges();
    jest.spyOn(modalService, 'open').mockReturnValue(modalRef);
    component.showHelp();
    expect(modalService.open).toHaveBeenCalledWith('Error: invalid modal content!', {
      size: 'lg',
      centered: true
    });

    modalRef.close();
  });
});
