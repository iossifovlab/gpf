import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetComponentErrors {
  public static readonly type = '[Error handling] Set component errors';
  public constructor(
    public componentId: string, public errors: Array<string>
  ) {}
}

export interface ErrorsModel {
  componentErrors: Map<string, Array<string>>;
}

@State<ErrorsModel>({
  name: 'errorsState',
  defaults: {
    componentErrors: new Map<string, Array<string>>()
  },
})
@Injectable()
export class ErrorsState {
  @Action(SetComponentErrors)
  public setComponentErrors(ctx: StateContext<ErrorsModel>, action: SetComponentErrors): void {
    const errors: Map<string, Array<string>> = ctx.getState().componentErrors;
    if (action.errors.length) {
      errors.set(action.componentId, action.errors);
    } else {
      errors.delete(action.componentId);
    }
    ctx.patchState({ componentErrors: errors });
  }
}
