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
  $autismGeneToolConfig: Observable<AgpConfig>;
  geneSymbol: string;

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private route: ActivatedRoute,
  ) { }

  ngOnInit(): void {
    this.$autismGeneToolConfig = this.autismGeneProfilesService.getConfig();
  }

  ngAfterViewInit(): void {
    this.geneSymbol = this.route.snapshot.params.gene.toUpperCase();
  }
}
