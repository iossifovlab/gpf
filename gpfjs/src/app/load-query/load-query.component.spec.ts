import { HttpClient, HttpHandler } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { QueryService } from 'app/query/query.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { LoadQueryComponent } from './load-query.component';
import { StoreModule } from '@ngrx/store';
import { errorsReducer } from 'app/common/errors.state';

describe('LoadQueryComponent', () => {
  let component: LoadQueryComponent;
  let fixture: ComponentFixture<LoadQueryComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [LoadQueryComponent],
      providers: [
        QueryService,
        HttpClient,
        HttpHandler,
        ConfigService,
        DatasetsService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        RouterTestingModule,
        StoreModule.forRoot({errors: errorsReducer})
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LoadQueryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
