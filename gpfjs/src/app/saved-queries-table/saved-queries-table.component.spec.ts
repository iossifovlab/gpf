import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { QueryService } from 'app/query/query.service';
import { ResizeService } from 'app/table/resize.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';

import { SavedQueriesTableComponent } from './saved-queries-table.component';
import { Observable, of } from 'rxjs';
import { StoreModule } from '@ngrx/store';

class MockQueryService {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public deleteQuery(uuid: string): Observable<void> {
    return of();
  }
}

describe('SavedQueriesTableComponent', () => {
  let component: SavedQueriesTableComponent;
  let fixture: ComponentFixture<SavedQueriesTableComponent>;
  const queriesMock = [
    {
      name: 'name1',
      description: 'desc1',
      page: 'page1',
      uuid: 'uuid1',
      url: 'url1',
    },
    {
      name: 'name2',
      description: 'desc2',
      page: 'page2',
      uuid: 'uuid2',
      url: 'url2',
    },
    {
      name: 'name3',
      description: 'desc3',
      page: 'page3',
      uuid: 'uuid3',
      url: 'url3',
    }
  ];

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        SavedQueriesTableComponent,
      ],
      providers: [
        {provide: QueryService, useValue: new MockQueryService()},
        ConfigService,
        ResizeService,
        DatasetsService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClientTesting()
      ],
      imports: [RouterTestingModule, StoreModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(SavedQueriesTableComponent);
    component = fixture.componentInstance;
    component.queries = queriesMock;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should delete query', () => {
    component.queries = queriesMock;
    component.deleteQuery('uuid2');
    expect(component.queries).toStrictEqual([
      {
        name: 'name1',
        description: 'desc1',
        page: 'page1',
        uuid: 'uuid1',
        url: 'url1',
      },
      {
        name: 'name3',
        description: 'desc3',
        page: 'page3',
        uuid: 'uuid3',
        url: 'url3',
      }
    ]);

    component.queries = queriesMock;
    component.deleteQuery('uuid1');
    component.deleteQuery('uuid3');
    expect(component.queries).toStrictEqual([
      {
        name: 'name2',
        description: 'desc2',
        page: 'page2',
        uuid: 'uuid2',
        url: 'url2',
      }
    ]);
  });
});
