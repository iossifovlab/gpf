import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { UsersService } from 'app/users/users.service';
import { FederationCredential } from './federation-credentials';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-federation-credentials',
  templateUrl: './federation-credentials.component.html',
  styleUrls: ['../saved-queries-table/saved-queries-table.component.css', './federation-credentials.component.css']
})
export class FederationCredentialsComponent implements OnInit {
  public credentials: FederationCredential[];
  public creationError = '';
  public modal: NgbModalRef;
  public temporaryShownCredentials = '';
  @ViewChild('credentialModal') public credentialModal;
  @ViewChild('credentialNameBox') public newCredentialName: ElementRef;

  public constructor(
    private usersService: UsersService,
    private modalService: NgbModal
  ) {}

  public ngOnInit(): void {
    this.usersService.getFederationCredentials().subscribe(res => {
      this.credentials = res;
    });
  }

  public deleteCredential(name: string): void {
    //hehe
  }

  public createCredential(name: string): void {
    if (!(new RegExp(/.{3,}/)).test(String(name).toLowerCase())) {
      (this.newCredentialName.nativeElement as HTMLInputElement).focus();
      this.creationError = 'Credential names must be at least 3 symbols long.';
      return;
    }
    this.usersService.createFederationCredentials(name).subscribe(credentials => {
      this.temporaryShownCredentials = credentials;
      this.openModal();
    });
  }

  private openModal(): void {
    if (this.modalService.hasOpenModals()) {
      return;
    }
    this.modal = this.modalService.open(
      this.credentialModal,
      {animation: false, centered: true, size: 'lg', windowClass: 'credential-modal'}
    );
  }

  public closeModal(): void {
    this.modal.close();
    this.temporaryShownCredentials = '';
  }
}
