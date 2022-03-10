import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { QueryService } from 'app/query/query.service';
import { RouterTestingModule } from '@angular/router/testing';
import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { NgxsModule } from '@ngxs/store';

describe('AutismGeneProfilesBlockComponent', () => {
  let component: AutismGeneProfilesBlockComponent;
  let fixture: ComponentFixture<AutismGeneProfilesBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfilesBlockComponent ],
      providers: [ConfigService, QueryService, DatasetsService, UsersService],
      imports: [HttpClientTestingModule, NgbNavModule, RouterTestingModule, NgxsModule.forRoot()]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
