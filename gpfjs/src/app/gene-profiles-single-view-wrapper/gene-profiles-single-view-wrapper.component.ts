import { AfterViewInit, Component, Input, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { GeneProfilesService } from 'app/gene-profiles-block/gene-profiles.service';
import { GeneProfilesSingleViewConfig } from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { Observable } from 'rxjs';
import { Location } from '@angular/common';

@Component({
  selector: 'gpf-gene-profiles-single-view-wrapper',
  templateUrl: './gene-profiles-single-view-wrapper.component.html',
  styleUrls: ['./gene-profiles-single-view-wrapper.component.css'],
  standalone: false
})
export class GeneProfileSingleViewWrapperComponent implements OnInit, AfterViewInit {
  public $geneProfilesConfig: Observable<GeneProfilesSingleViewConfig>;
  @Input() public geneSymbols = new Set<string>();

  public constructor(
    private geneProfilesService: GeneProfilesService,
    private route: ActivatedRoute,
    private location: Location
  ) { }

  public ngOnInit(): void {
    this.$geneProfilesConfig = this.geneProfilesService.getConfig();
  }

  public ngAfterViewInit(): void {
    if (this.geneSymbols.size) {
      this.location.replaceState('gene-profiles/' + Array.from(this.geneSymbols).toString());
    } else {
      this.geneSymbols = new Set(
        (this.route.snapshot.params.genes as string)
          .split(',')
          .filter(p => p)
          .map(p => p.trim())
      );
      this.location.replaceState('gene-profiles/' + Array.from(this.geneSymbols).toString());
    }
  }
}
