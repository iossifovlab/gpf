import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';
import { GpfTableSubcontentComponent } from 'app/table/component/subcontent.component';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableCellComponent } from 'app/table/view/cell.component';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { UsersService } from 'app/users/users.service';
import { DatasetsTableComponent } from './datasets-table.component';
import { GpfTableHeaderCellComponent } from 'app/table/view/header/header-cell.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { ResizeService } from 'app/table/resize.service';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NgxsModule } from '@ngxs/store';

describe('DatasetsTableComponent', () => {
  let component: DatasetsTableComponent;
  let fixture: ComponentFixture<DatasetsTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        DatasetsTableComponent,
        GpfTableComponent,
        GpfTableCellComponent,
        GpfTableColumnComponent,
        GpfTableEmptyCellComponent,
        GpfTableContentHeaderComponent,
        GpfTableSubcontentComponent,
        GpfTableContentComponent,
        GpfTableSubcontentComponent,
        GpfTableHeaderCellComponent,
        GpfTableHeaderComponent
      ],
      providers: [
        ConfigService,
        DatasetsService,
        UsersService,
        UsersGroupsService,
        ResizeService
      ],
      imports: [
        RouterTestingModule,
        HttpClientTestingModule,
        NgxsModule.forRoot([])
      ],
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DatasetsTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
