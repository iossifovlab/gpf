import { Component, forwardRef } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { PresentInRole } from 'app/datasets/datasets';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { PhenoToolEffectTypesComponent } from 'app/pheno-tool-effect-types/pheno-tool-effect-types.component';
import { PresentInParentComponent } from 'app/present-in-parent/present-in-parent.component';
import { QueryStateProvider } from 'app/query/query-state-provider';
import { StateRestoreService } from 'app/store/state-restore.service';
import { Input } from 'hammerjs';
import { Observable } from 'rxjs';

import { PresentInRoleComponent } from './present-in-role.component';

@Component({
  selector: 'gpf-present-in-role',
  templateUrl: './present-in-role.component.html',
  styleUrls: ['./present-in-role.component.css'],
  providers: [{
    provide: QueryStateProvider, useExisting: forwardRef(() => PresentInRoleComponent) }]
})
export class MockPresentInRoleComponent extends PresentInRoleComponent {
  presentInRole = new PresentInRole('', '', ['']);

  ngOnInit() {}
  constructor() { super(undefined); }
  selectAll(): void {}
  selectNone(): void {}
  presentInRoleCheckValue(key: string, value: boolean): void {}
  getState() {
    return new Observable<{presentInRole: {[x: string]: unknown[]; }; }>();
  }
}

describe('PresentInRoleComponent', () => {
  let component: MockPresentInRoleComponent;
  let fixture: ComponentFixture<MockPresentInRoleComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MockPresentInRoleComponent, ErrorsAlertComponent, PresentInParentComponent, PhenoToolEffectTypesComponent],
      providers: [StateRestoreService, {provide: Observable, useValue: new Observable()}]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MockPresentInRoleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
