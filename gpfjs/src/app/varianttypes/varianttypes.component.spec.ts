/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { VarianttypesComponent } from './varianttypes.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';


describe('VarianttypesComponent', () => {
  let component: VarianttypesComponent;
  let fixture: ComponentFixture<VarianttypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [VarianttypesComponent, ErrorsAlertComponent],
      providers: [StateRestoreService, DatasetsService, ConfigService, UsersService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VarianttypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
