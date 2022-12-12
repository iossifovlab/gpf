import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { QueryService } from 'app/query/query.service';
import { SavedQueriesTableComponent } from 'app/saved-queries-table/saved-queries-table.component';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { ResizeService } from 'app/table/resize.service';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableHeaderCellComponent } from 'app/table/view/header/header-cell.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';

import { SavedQueriesComponent } from './saved-queries.component';

describe('SavedQueriesComponent', () => {
  let component: SavedQueriesComponent;
  let fixture: ComponentFixture<SavedQueriesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        SavedQueriesComponent,
        SavedQueriesTableComponent,
        GpfTableComponent,
        GpfTableContentComponent,
        GpfTableContentHeaderComponent,
        GpfTableColumnComponent,
        GpfTableHeaderCellComponent,
        GpfTableEmptyCellComponent,
        GpfTableHeaderCellComponent,
        GpfTableHeaderComponent
      ],
      providers: [
        QueryService, ConfigService, UsersService, ResizeService, DatasetsService,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        RouterTestingModule, HttpClientTestingModule, NgbNavModule, NgxsModule.forRoot([], {developmentMode: true})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SavedQueriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
