import { Input, Component, OnInit } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngrx/store';
import { selectVariantTypes, setVariantTypes } from './variant-types.state';
import { ComponentValidator } from 'app/common/component-validator';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-variant-types',
  templateUrl: './variant-types.component.html',
  styleUrls: ['./variant-types.css']
})
export class VariantTypesComponent extends ComponentValidator implements OnInit {
  @Input() public variantTypes: Set<string> = new Set<string>([]);

  @Input()
  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedVariantTypes: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, 'variantTypes', selectVariantTypes);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.select(selectVariantTypes).pipe(take(1)).subscribe(variantTypesState => {
      this.selectedVariantTypes = new Set(variantTypesState);
    });
  }

  public updateVariantTypes(newValues: Set<string>): void {
    this.selectedVariantTypes = newValues;
    this.store.dispatch(setVariantTypes({ variantTypes: [...newValues] }));
  }
}
