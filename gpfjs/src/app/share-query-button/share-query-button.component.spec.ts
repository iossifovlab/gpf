import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { QueryService } from 'app/query/query.service';
import { UsersService } from 'app/users/users.service';

import { ShareQueryButtonComponent } from './share-query-button.component';

describe('ShareQueryButtonComponent', () => {
  let component: ShareQueryButtonComponent;
  let fixture: ComponentFixture<ShareQueryButtonComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ShareQueryButtonComponent],
      providers: [
        DatasetsService,
        ConfigService,
        UsersService,
        QueryService,
      ],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([])]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ShareQueryButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
