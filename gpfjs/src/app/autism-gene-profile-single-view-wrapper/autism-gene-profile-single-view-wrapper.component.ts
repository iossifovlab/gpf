import { AfterViewInit, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { AgpConfig } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-autism-gene-profile-single-view-wrapper',
  templateUrl: './autism-gene-profile-single-view-wrapper.component.html',
  styleUrls: ['./autism-gene-profile-single-view-wrapper.component.css']
})
export class AutismGeneProfileSingleViewWrapperComponent implements OnInit, AfterViewInit {
  public $autismGeneToolConfig: Observable<AgpConfig>;
  public geneSymbols = new Set<string>();

  public constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private route: ActivatedRoute
  ) { }

  public ngOnInit(): void {
    this.$autismGeneToolConfig = this.autismGeneProfilesService.getConfig();
  }

  public ngAfterViewInit(): void {
    this.geneSymbols = new Set(
      this.route.snapshot.params.genes
        .split(',')
        .filter(p => p)
        .map(p => p.trim().toUpperCase())
    );
  }
}
