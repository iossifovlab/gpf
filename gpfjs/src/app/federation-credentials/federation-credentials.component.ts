import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { UsersService } from 'app/users/users.service';
import { FederationCredential, FederationPostJson } from './federation-credentials';
import { NgbModal, NgbModalRef, NgbTooltip } from '@ng-bootstrap/ng-bootstrap';
import { concatMap, debounceTime, fromEvent, of, tap, zip } from 'rxjs';

@Component({
  selector: 'gpf-federation-credentials',
  templateUrl: './federation-credentials.component.html',
  styleUrls: ['../saved-queries-table/saved-queries-table.component.css', './federation-credentials.component.css'],
  standalone: false
})
export class FederationCredentialsComponent implements OnInit {
  public credentials: FederationCredential[];
  public creationError = '';
  public renameError = '';
  public modal: NgbModalRef;
  public temporaryShownFederationCredentials: FederationPostJson;
  @ViewChild('credentialModal') public credentialModal: ElementRef;
  @ViewChild('credentialNameBox') public newCredentialName: ElementRef;
  @ViewChild('credentialRename') public credentialRename: ElementRef;
  @ViewChild('createButton') public createButton: ElementRef;
  private copiedTimeoutHandle: NodeJS.Timeout;
  public currentCredentialEdit = '';

  public constructor(
    private usersService: UsersService,
    private modalService: NgbModal,
  ) { }

  public ngOnInit(): void {
    this.usersService.getFederationCredentials().subscribe(res => {
      this.credentials = res;

      fromEvent(this.createButton.nativeElement as HTMLElement, 'click').pipe(
        debounceTime(250),
        tap(() => {
          this.createCredential((this.newCredentialName.nativeElement as HTMLInputElement).value);
        })
      ).subscribe();
    });
  }

  public deleteCredential(name: string): void {
    this.usersService.deleteFederationCredentials(name).pipe(
      concatMap(() => this.usersService.getFederationCredentials())
    ).subscribe(res => {
      this.credentials = res;
    });
  }

  public createCredential(name: string): void {
    if (!new RegExp(/.{3,}/).test(String(name).toLowerCase())) {
      (this.newCredentialName.nativeElement as HTMLInputElement).focus();
      this.creationError = 'Credential names must be at least 3 symbols long.';
      return;
    }

    if (this.credentials.find(credential => credential.name === name) !== undefined) {
      (this.newCredentialName.nativeElement as HTMLInputElement).focus();
      this.creationError = 'Credential with such name already exists!';
      return;
    }

    this.creationError = '';

    this.usersService.createFederationCredentials(name).pipe(
      concatMap(
        (federationCredentials: FederationPostJson) => zip(
          of(federationCredentials), this.usersService.getFederationCredentials()
        )
      )
    ).subscribe(([federationCredentials, allFederationCredentials]) => {
      this.credentials = allFederationCredentials;
      this.temporaryShownFederationCredentials = federationCredentials;
      (this.newCredentialName.nativeElement as HTMLInputElement).value = '';
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

  public edit(credential: FederationCredential, newName: string): void {
    if (this.credentials.find(cred => cred.name === newName) !== undefined) {
      this.renameError = 'Credential with such name already exists!';
      return;
    }
    if (!newName.trim()) {
      this.renameError = 'Please fill the field!';
      return;
    }
    this.usersService.updateFederationCredentials(credential.name, newName)
      .subscribe((res: string) => {
        credential.name = res;
      });
    this.currentCredentialEdit = '';
  }

  public openCopiedTooltip(tooltip: NgbTooltip): void {
    tooltip.autoClose = true;
    tooltip.open();
    window.clearTimeout(this.copiedTimeoutHandle);
    this.copiedTimeoutHandle = setTimeout(() => {
      tooltip.close();
    }, 2000);
  }
}
