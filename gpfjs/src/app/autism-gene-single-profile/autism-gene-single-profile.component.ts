import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { AutismGeneToolConfig, AutismGeneToolGene } from 'app/autism-gene-profiles/autism-gene-profile';
import { Observable } from 'rxjs';
import { AutismGeneSingleProfileService } from './autism-gene-single-profile.service';

@Component({
  selector: 'gpf-autism-gene-single-profile',
  templateUrl: './autism-gene-single-profile.component.html',
  styleUrls: ['./autism-gene-single-profile.component.css']
})
export class AutismGeneSingleProfileComponent implements OnInit, OnChanges {
  @Input() readonly geneSymbol: string;
  @Input() config: AutismGeneToolConfig;

  private gene$: Observable<AutismGeneToolGene>;
  private geneLists: string[];

  constructor(
    private autismGeneSingleProfileService: AutismGeneSingleProfileService,
  ) { }

  ngOnChanges(): void {
    if (this.config) {
      this.geneLists = this.config['geneLists'];
    }
  }

  ngOnInit(): void {
    this.gene$ = this.autismGeneSingleProfileService.getGene(this.geneSymbol);
  }
}
