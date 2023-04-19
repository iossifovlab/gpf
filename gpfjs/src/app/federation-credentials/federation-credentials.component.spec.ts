import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FederationCredentialsComponent } from './federation-credentials.component';

describe('FederationCredentialsComponent', () => {
  let component: FederationCredentialsComponent;
  let fixture: ComponentFixture<FederationCredentialsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FederationCredentialsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FederationCredentialsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
