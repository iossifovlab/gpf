import { Component, Input, OnInit } from '@angular/core';
import { AutismGeneToolGene } from 'app/autism-gene-profiles/autism-gene-profile';
import { AutismGeneSingleProfileService } from './autism-gene-single-profile.service';

@Component({
  selector: 'gpf-autism-gene-single-profile',
  templateUrl: './autism-gene-single-profile.component.html',
  styleUrls: ['./autism-gene-single-profile.component.css']
})
export class AutismGeneSingleProfileComponent implements OnInit {
  @Input() readonly geneSymbol: string;
  private gene: AutismGeneToolGene;

  constructor(
    private autismGeneSingleProfileService: AutismGeneSingleProfileService,
  ) { }

  ngOnInit(): void {
    this.autismGeneSingleProfileService.getGene(this.geneSymbol).take(1).subscribe(res => {
      this.gene = res;
      console.log(this.gene)
    });
  }

}
