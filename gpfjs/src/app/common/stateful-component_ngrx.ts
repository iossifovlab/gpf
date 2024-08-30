import { OnDestroy, OnInit, Directive } from '@angular/core';
import { Observable, Subscription } from 'rxjs';
import { validate, ValidationError } from 'class-validator';
import { Selector, Store } from '@ngrx/store';
import { resetErrors, selectErrors, setErrors } from './errors.state';

@Directive()
export abstract class StatefulComponentNgRx implements OnInit, OnDestroy {
  protected componentStateSubscription: Subscription;
  protected errorsState$: Observable<object>;
  protected componentState$: Observable<unknown>;

  public errors: Array<string>;

  public constructor(
    protected store: Store,
    public readonly componentId: string,
    protected childStateSelector: Selector<unknown, unknown>,
  ) {
    this.errorsState$ = this.store.select(selectErrors);
    this.componentState$ = this.store.select(childStateSelector);
    this.errors = [];
  }

  public ngOnInit(): void {
    this.componentStateSubscription = this.componentState$.subscribe(() => {
      // validate for errors
      validate(this, { forbidUnknownValues: true }).then(errors => {
        if (errors.length) {
          this.errors = this.errorsToMessages(errors);
          this.store.dispatch(setErrors({
            errors: {
              componentId: this.componentId, errors: this.errors
            }
          }));
        } else {
          this.errors = [];
          this.store.dispatch(resetErrors({componentId: this.componentId}));
        }
      });
    });
  }

  public ngOnDestroy(): void {
    if (this.componentStateSubscription) {
      this.store.dispatch(resetErrors({componentId: this.componentId}));
      this.componentStateSubscription.unsubscribe();
      this.componentStateSubscription = null;
    }
  }

  private errorsToMessages(errors: Array<ValidationError>): Array<string> {
    let messages = new Array<string>();
    for (const error of errors) {
      if (error.constraints !== undefined) {
        messages.push(this.errorToMessage(error));
      }
      if (error.children && error.children.length) {
        messages = [...messages, ...this.errorsToMessages(error.children)];
      }
    }
    return messages;
  }

  private errorToMessage(error: ValidationError): string {
    return Object.values(error.constraints).join('\n');
  }
}
