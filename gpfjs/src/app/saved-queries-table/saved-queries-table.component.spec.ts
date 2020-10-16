import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
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

import { SavedQueriesTableComponent } from './saved-queries-table.component';

describe('SavedQueriesTableComponent', () => {
  let component: SavedQueriesTableComponent;
  let fixture: ComponentFixture<SavedQueriesTableComponent>;

  beforeEach(async(() => {
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
      providers: [QueryService, ConfigService, ResizeService],
      imports: [RouterTestingModule, HttpClientTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SavedQueriesTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
