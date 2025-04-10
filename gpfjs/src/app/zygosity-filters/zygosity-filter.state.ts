import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';

export const zygosityFilterInitialState: ZygosityFilterState[] = [];

export interface ZygosityFilterState {
  componentId: string,
  filter: string
}

export const selectZygosityFilter = createFeatureSelector<ZygosityFilterState[]>('zygosityFilter');

export const setZygosityFilter = createAction(
  '[Genotype] Set zygosity filter',
  props<{ zygosityFilter: ZygosityFilterState }>()
);

export const setAllZygosityFilters = createAction(
  '[Genotype] Set all zygosity filters',
  props<{ zygosityFilters: ZygosityFilterState[] }>()
);

export const resetZygosityFilter = createAction(
  '[Genotype] Reset zygosity filter',
  props<{ componentId: string }>()
);

export const zygosityFilterReducer = createReducer(
  zygosityFilterInitialState,
  on(setAllZygosityFilters, (state, { zygosityFilters }) => {
    return zygosityFilters ? [...zygosityFilters] : zygosityFilterInitialState;
  }),
  on(setZygosityFilter, (state, { zygosityFilter }) => {
    let updatedState = cloneDeep(state);
    const currentIndex = state.findIndex(e => e.componentId === zygosityFilter.componentId);

    if (currentIndex === -1) {
      updatedState = [...state, cloneDeep(zygosityFilter)];
      return updatedState;
    }

    updatedState[currentIndex].filter = zygosityFilter.filter;

    return updatedState;
  }),
  on(resetZygosityFilter, (state, { componentId }) => state.filter(z => z.componentId !== componentId)),
);
