import { Tab, Tabs } from '@mui/material';
import { useState } from 'react';

import { brandsApi, categoriesApi, groupsApi, subgroupsApi } from '@/api/endpoints';
import CatalogCrud from '@/components/CatalogCrud';

const TABS = [
  { label: 'Categorias', api: categoriesApi, key: 'categories', perm: 'category' },
  { label: 'Grupos', api: groupsApi, key: 'groups', perm: 'group' },
  { label: 'Subgrupos', api: subgroupsApi, key: 'subgroups', perm: 'subgroup' },
  { label: 'Marcas', api: brandsApi, key: 'brands', perm: 'brand' },
] as const;

export default function CategoriesPage() {
  const [tab, setTab] = useState(0);
  const current = TABS[tab];

  return (
    <>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }} variant="scrollable">
        {TABS.map((t) => (
          <Tab key={t.key} label={t.label} />
        ))}
      </Tabs>
      <CatalogCrud
        key={current.key}
        title={current.label}
        subtitle="Cadastro independente de classificação de produtos"
        api={current.api}
        queryKey={current.key}
        permission={current.perm}
      />
    </>
  );
}
