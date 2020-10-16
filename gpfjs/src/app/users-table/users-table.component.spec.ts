import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { GpfTableSubcontentComponent } from 'app/table/component/subcontent.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { ResizeService } from 'app/table/resize.service';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableCellComponent } from 'app/table/view/cell.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableHeaderCellComponent } from 'app/table/view/header/header-cell.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { UsersService } from 'app/users/users.service';

import { UsersTableComponent } from './users-table.component';

describe('UsersTableComponent', () => {
  let component: UsersTableComponent;
  let fixture: ComponentFixture<UsersTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        UsersTableComponent,
        GpfTableComponent,
        GpfTableColumnComponent,
        GpfTableContentComponent,
        GpfTableHeaderComponent,
        GpfTableCellComponent,
        GpfTableContentHeaderComponent,
        GpfTableEmptyCellComponent,
        GpfTableHeaderCellComponent,
        GpfTableSubheaderComponent,
        GpfTableSubcontentComponent
      ],
      providers: [UsersService, ConfigService, ResizeService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UsersTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
