import { Component } from '@angular/core';
import { configMock, rowMock } from './agp-table';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { take } from 'rxjs/operators';

@Component({
  selector: 'gpf-agp-table',
  templateUrl: './agp-table.component.html',
  styleUrls: ['./agp-table.component.css']
})
export class AgpTableComponent {

  public sortBy: string;
  public orderBy: string;
  private pageIndex = 1;
  public currentSortingColumnId: string;

  public config;
  public genes = [];

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  public ngOnInit(): void {
    this.autismGeneProfilesService.getConfigNew().pipe(take(1)).subscribe(config => {
      this.config = config;

      this.sortBy = `autism_gene_sets_rank`;
      this.orderBy = 'desc';
      this.currentSortingColumnId = this.sortBy;

      this.autismGeneProfilesService.getGenes(
        this.pageIndex, undefined, this.sortBy, this.orderBy
      ).pipe(take(1)).subscribe(res => {
        this.genes = this.genes.concat(res);
      });
    });

  }
}
