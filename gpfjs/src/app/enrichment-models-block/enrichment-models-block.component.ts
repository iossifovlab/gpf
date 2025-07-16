import { Component, Input } from '@angular/core';

@Component({
    selector: 'gpf-enrichment-models-block',
    templateUrl: './enrichment-models-block.component.html',
    standalone: false
})
export class EnrichmentModelsBlockComponent {
  @Input() public selectedDatasetId: string;
}
