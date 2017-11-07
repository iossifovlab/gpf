import { TestBed, inject } from '@angular/core/testing';

import { UsersGroupsService } from './users-groups.service';

describe('UsersGroupsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UsersGroupsService]
    });
  });

  it('should ...', inject([UsersGroupsService], (service: UsersGroupsService) => {
    expect(service).toBeTruthy();
  }));
});
