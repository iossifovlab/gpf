import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { GpfTableSubcontentComponent } from 'app/table/component/subcontent.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { ResizeService } from 'app/table/resize.service';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableHeaderCellComponent } from 'app/table/view/header/header-cell.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { UsersTableComponent } from 'app/users-table/users-table.component';
import { UsersService } from 'app/users/users.service';

import { UserManagementComponent } from './user-management.component';

describe('UserManagementComponent', () => {
  let component: UserManagementComponent;
  let fixture: ComponentFixture<UserManagementComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        UserManagementComponent,
        UsersTableComponent,
        GpfTableComponent,
        GpfTableContentComponent,
        GpfTableSubcontentComponent,
        GpfTableHeaderComponent,
        GpfTableHeaderCellComponent,
        GpfTableSubheaderComponent,
        GpfTableContentHeaderComponent,
        GpfTableColumnComponent,
        GpfTableEmptyCellComponent
      ],
      providers: [UsersService, ConfigService, ResizeService],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NgbNavModule,
        FormsModule,
        NgxsModule.forRoot([], {developmentMode: true})
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UserManagementComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
