import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed, inject } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';

import { UsersGroupsService } from './users-groups.service';

describe('UsersGroupsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UsersGroupsService, ConfigService],
      imports: [HttpClientTestingModule]
    });
  });

  it('should ...', inject([UsersGroupsService], (service: UsersGroupsService) => {
    expect(service).toBeTruthy();
  }));
});
