import { OnDestroy, OnInit, Directive } from "@angular/core";
import { Observable, Subscription } from "rxjs";
import { SetComponentErrors } from "./errors.state";
import { validate, ValidationError } from "class-validator";
import { Store } from "@ngxs/store";

@Directive()
export abstract class StatefulComponent implements OnInit, OnDestroy {
  protected stateSubscription: Subscription;
  protected state$: Observable<object>;
  public errors: Array<string>;

  constructor(
    protected store: Store,
    protected stateSelector,
    readonly componentId: string,
  ) {
    this.state$ = this.store.select(this.stateSelector);
    this.errors = new Array();
  }

  ngOnInit() {
    this.stateSubscription = this.state$.subscribe(_ => {
      // validate for errors
      validate(this, { forbidUnknownValues: true }).then(errors => {
        this.errors = this.errorsToMessages(errors);
        this.store.dispatch(new SetComponentErrors(this.componentId, this.errors));
      });
    });
  }

  ngOnDestroy() {
    if (this.stateSubscription) {
      this.store.dispatch(new SetComponentErrors(this.componentId, new Array()));
      this.stateSubscription.unsubscribe();
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
