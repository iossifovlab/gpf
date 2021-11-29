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
  public geneSymbol: string;

  public constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private route: ActivatedRoute
  ) { }

  public ngOnInit(): void {
    this.$autismGeneToolConfig = this.autismGeneProfilesService.getConfig();
  }

  public ngAfterViewInit(): void {
    if (this.route.snapshot.params.gene instanceof String) {
      this.geneSymbol = this.route.snapshot.params.gene.toUpperCase();
    }
  }
}
