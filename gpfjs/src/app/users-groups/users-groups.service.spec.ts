import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed, inject } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersGroupsService } from './users-groups.service';
import { provideHttpClient } from '@angular/common/http';

describe('UsersGroupsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UsersGroupsService, ConfigService, provideHttpClient(), provideHttpClientTesting()],
      imports: []
    });
  });

  it('should ...', inject([UsersGroupsService], (service: UsersGroupsService) => {
    expect(service).toBeTruthy();
  }));
});
