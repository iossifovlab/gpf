import { Component, Input, OnInit } from '@angular/core';
import { AutismGeneToolGene } from 'app/autism-gene-profiles/autism-gene-profile';
import { Observable } from 'rxjs';
import { AutismGeneSingleProfileService } from './autism-gene-single-profile.service';

@Component({
  selector: 'gpf-autism-gene-single-profile',
  templateUrl: './autism-gene-single-profile.component.html',
  styleUrls: ['./autism-gene-single-profile.component.css']
})
export class AutismGeneSingleProfileComponent implements OnInit {
  @Input() readonly geneSymbol: string;
  private gene$: Observable<AutismGeneToolGene>;

  constructor(
    private autismGeneSingleProfileService: AutismGeneSingleProfileService,
  ) { }

  ngOnInit(): void {
    this.gene$ = this.autismGeneSingleProfileService.getGene(this.geneSymbol);
  }
}
