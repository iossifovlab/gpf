/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { RegionsBlockComponent } from './regions-block.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

describe('RegionsBlockComponent', () => {
  let component: RegionsBlockComponent;
  let fixture: ComponentFixture<RegionsBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [RegionsBlockComponent],
      providers: [StateRestoreService],
      imports: [NgbModule, RouterTestingModule],
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RegionsBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
