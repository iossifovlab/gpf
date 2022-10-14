import { APP_BASE_HREF } from '@angular/common';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
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
import { GpfTableNothingFoundRowComponent } from 'app/table/view/nothing-found-row.component';
import { UsersService } from 'app/users/users.service';

import { UsersTableComponent } from './users-table.component';

describe('UsersTableComponent', () => {
  let component: UsersTableComponent;
  let fixture: ComponentFixture<UsersTableComponent>;

  beforeEach(waitForAsync(() => {
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
        GpfTableSubcontentComponent,
        GpfTableNothingFoundRowComponent
      ],
      providers: [UsersService, ConfigService, ResizeService, { provide: APP_BASE_HREF, useValue: '' }],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})]
    }).compileComponents();
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
