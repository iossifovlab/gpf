import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddItem {
  static readonly type = '[Checkbox list] Add item';
  constructor(public item: string) {}
}

export class RemoveItem {
  static readonly type = '[Checkbox list] Remove item';
  constructor(public item: string) {}
}

export class SetItems {
  static readonly type = '[Checkbox list] Set items';
  constructor(public items: Set<string>) {}
}

export interface CheckboxListModel {
  items: string[];
}

@State<CheckboxListModel>({
  name: 'checkboxListState',
  defaults: {
    items: []
  },
})
@Injectable()
export class CheckboxListState {
  @Action(AddItem)
  addItem(ctx: StateContext<CheckboxListModel>, action: AddItem) {
    const state = ctx.getState();
    ctx.patchState({
      items: [...state.items, action.item]
    });
  }

  @Action(RemoveItem)
  removeItem(ctx: StateContext<CheckboxListModel>, action: RemoveItem) {
    const state = ctx.getState();
    ctx.patchState({
      items: state.items.filter(item => item !== action.item)
    });
  }

  @Action(SetItems)
  setItems(ctx: StateContext<CheckboxListModel>, action: SetItems) {
    const state = ctx.getState();
    ctx.patchState({
      items: Array.from(action.items)
    });
  }
}
