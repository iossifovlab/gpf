import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { QueryService } from 'app/query/query.service';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { ResizeService } from 'app/table/resize.service';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableCellComponent } from 'app/table/view/cell.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableHeaderCellComponent } from 'app/table/view/header/header-cell.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { UsersService } from 'app/users/users.service';

import { SavedQueriesTableComponent } from './saved-queries-table.component';

describe('SavedQueriesTableComponent', () => {
  let component: SavedQueriesTableComponent;
  let fixture: ComponentFixture<SavedQueriesTableComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        SavedQueriesTableComponent,
        GpfTableComponent,
        GpfTableColumnComponent,
        GpfTableContentComponent,
        GpfTableHeaderComponent,
        GpfTableCellComponent,
        GpfTableContentHeaderComponent,
        GpfTableEmptyCellComponent,
        GpfTableHeaderCellComponent,
      ],
      providers: [
        QueryService, ConfigService, ResizeService, DatasetsService, UsersService
      ],
      imports: [RouterTestingModule, HttpClientTestingModule, NgxsModule.forRoot([], {developmentMode: true})]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SavedQueriesTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should delete query', () => {
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

    component.queries = queriesMock;
    component.deleteQuery('uuid2');
    expect(component.queries).toEqual([
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
    expect(component.queries).toEqual([
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
