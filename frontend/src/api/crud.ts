import { api } from './client';
import type { Page } from './types';

export interface ListParams {
  page?: number;
  size?: number;
  q?: string;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
  [key: string]: unknown;
}

/** Factory returning typed CRUD helpers bound to a REST resource path. */
export function createCrudApi<T, TCreate = Partial<T>, TUpdate = Partial<T>>(resource: string) {
  return {
    list: async (params: ListParams = {}): Promise<Page<T>> => {
      const { data } = await api.get<Page<T>>(resource, { params });
      return data;
    },
    get: async (id: number): Promise<T> => {
      const { data } = await api.get<T>(`${resource}/${id}`);
      return data;
    },
    create: async (payload: TCreate): Promise<T> => {
      const { data } = await api.post<T>(resource, payload);
      return data;
    },
    update: async (id: number, payload: TUpdate): Promise<T> => {
      const { data } = await api.put<T>(`${resource}/${id}`, payload);
      return data;
    },
    remove: async (id: number): Promise<void> => {
      await api.delete(`${resource}/${id}`);
    },
  };
}
