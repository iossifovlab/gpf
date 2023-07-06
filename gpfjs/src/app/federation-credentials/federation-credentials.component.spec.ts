import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FederationCredentialsComponent } from './federation-credentials.component';
import { Observable, of } from 'rxjs';
import { FederationCredential } from './federation-credentials';
import { UsersService } from 'app/users/users.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';

class MockUsersService {
  private credentials = [
    new FederationCredential('name1'),
    new FederationCredential('name2'),
    new FederationCredential('name3')
  ];

  public getFederationCredentials(): Observable<FederationCredential[]> {
    return of(this.credentials);
  }

  public deleteFederationCredentials(name: string): Observable<null> {
    this.credentials = this.credentials.filter(credential => credential.name !== name);

    return of(null);
  }

  public createFederationCredentials(name: string): Observable<string> {
    this.credentials.push(new FederationCredential(name));
    return of('secret new credential');
  }

  public updateFederationCredentials(oldName: string, newName: string): Observable<string> {
    return of(newName);
  }
}

describe('FederationCredentialsComponent', () => {
  let component: FederationCredentialsComponent;
  let fixture: ComponentFixture<FederationCredentialsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        FederationCredentialsComponent
      ],
      providers: [
        {provide: UsersService, useValue: new MockUsersService()}
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(FederationCredentialsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize credentials', () => {
    expect(component.credentials).toBeUndefined();
    component.ngOnInit();
    expect(component.credentials).toStrictEqual([
      new FederationCredential('name1'),
      new FederationCredential('name2'),
      new FederationCredential('name3')
    ]);
  });

  it('should delete credentials', () => {
    fixture.detectChanges();
    expect(component.credentials).toStrictEqual([
      new FederationCredential('name1'),
      new FederationCredential('name2'),
      new FederationCredential('name3')
    ]);

    component.deleteCredential('name2');
    expect(component.credentials).toStrictEqual([
      new FederationCredential('name1'),
      new FederationCredential('name3')
    ]);
  });

  it('should create credential', () => {
    fixture.detectChanges();
    expect(component.credentials).toStrictEqual([
      new FederationCredential('name1'),
      new FederationCredential('name2'),
      new FederationCredential('name3')
    ]);

    component.createCredential('');
    expect(component.credentials).toStrictEqual([
      new FederationCredential('name1'),
      new FederationCredential('name2'),
      new FederationCredential('name3')
    ]);

    component.createCredential('name4');
    fixture.detectChanges();
    expect(component.credentials).toStrictEqual([
      new FederationCredential('name1'),
      new FederationCredential('name2'),
      new FederationCredential('name3'),
      new FederationCredential('name4')
    ]);
    expect(component.temporaryShownCredentials).toBe('secret new credential');
    expect(document.getElementById('credential-modal-content').textContent).toBe('secret new credential');
  });

  it('should rename credential', () => {
    fixture.detectChanges();
    const credential = new FederationCredential('rename');
    component.edit(credential, 'newName');
    fixture.detectChanges();
    expect(credential.name).toBe('newName');
  });

  it('should not rename credential', () => {
    fixture.detectChanges();
    const credential = new FederationCredential('rename');
    component.edit(credential, '  ');
    fixture.detectChanges();
    expect(component.renameError).toBe('Please fill the field!');
    expect(credential.name).toBe('rename');

    component.edit(credential, 'name1');
    fixture.detectChanges();
    expect(component.renameError).toBe('Credential with such name already exists!');
    expect(credential.name).toBe('rename');
  });
});
