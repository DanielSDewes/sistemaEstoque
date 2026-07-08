import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import LightModeIcon from '@mui/icons-material/LightMode';
import LogoutIcon from '@mui/icons-material/Logout';
import MenuIcon from '@mui/icons-material/Menu';
import Warehouse from '@mui/icons-material/Warehouse';
import {
  AppBar,
  Avatar,
  Box,
  Collapse,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useEffect, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '@/auth/AuthContext';
import { isGroup, NAV_ITEMS, type NavEntry, type NavLeaf } from '@/navigation';
import { useColorMode } from '@/theme/ColorModeContext';

const DRAWER_WIDTH = 248;
const DRAWER_WIDTH_COLLAPSED = 76;
const COLLAPSE_KEY = 'estoque_sidebar_collapsed';

// Keep the drawer scrollable but hide the visible scrollbar (all browsers).
const HIDE_SCROLLBAR = {
  scrollbarWidth: 'none',
  '&::-webkit-scrollbar': { display: 'none' },
} as const;

export default function Layout() {
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const { mode, toggle: toggleColorMode } = useColorMode();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSE_KEY) === 'true');
  const { user, logout, hasPermission } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const canSee = (leaf: NavLeaf) => !leaf.permission || hasPermission(leaf.permission);
  // Filter leaves by permission and drop groups that end up empty.
  const tree: NavEntry[] = NAV_ITEMS.map((e) =>
    isGroup(e) ? { ...e, children: e.children.filter(canSee) } : e,
  ).filter((e) => (isGroup(e) ? e.children.length > 0 : canSee(e)));
  const leaves: NavLeaf[] = tree.flatMap((e) => (isGroup(e) ? e.children : [e]));

  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    NAV_ITEMS.forEach((e) => {
      if (isGroup(e)) init[e.label] = e.children.some((c) => c.path === window.location.pathname);
    });
    return init;
  });

  // Auto-open the group that owns the active route when navigating.
  useEffect(() => {
    const active = NAV_ITEMS.find(
      (e) => isGroup(e) && e.children.some((c) => c.path === location.pathname),
    );
    if (active && isGroup(active)) {
      setOpenGroups((prev) => ({ ...prev, [active.label]: true }));
    }
  }, [location.pathname]);

  const drawerWidth = collapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH;

  const toggleCollapsed = () =>
    setCollapsed((c) => {
      localStorage.setItem(COLLAPSE_KEY, String(!c));
      return !c;
    });

  const widthTransition = theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  });

  const go = (path: string) => {
    navigate(path);
    if (!isDesktop) setMobileOpen(false);
  };

  const leafButton = (leaf: NavLeaf, mini: boolean, nested: boolean) => {
    const active = location.pathname === leaf.path;
    const Icon = leaf.icon;
    return (
      <Tooltip key={leaf.path} title={mini ? leaf.label : ''} placement="right">
        <ListItemButton
          selected={active}
          onClick={() => go(leaf.path)}
          sx={{
            borderRadius: 2,
            mb: 0.5,
            justifyContent: mini ? 'center' : 'flex-start',
            px: mini ? 1.5 : 2,
            pl: !mini && nested ? 3.5 : undefined,
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              mr: mini ? 0 : 3,
              justifyContent: 'center',
              color: active ? 'primary.main' : undefined,
            }}
          >
            <Icon fontSize={nested && !mini ? 'small' : 'medium'} />
          </ListItemIcon>
          {!mini && <ListItemText primary={leaf.label} />}
        </ListItemButton>
      </Tooltip>
    );
  };

  // `mini` collapses labels to icons only (permanent desktop drawer). In mini
  // mode groups are flattened to icons since dropdowns can't expand inline.
  const renderDrawer = (mini: boolean) => (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflowX: 'hidden', ...HIDE_SCROLLBAR }}>
      <Toolbar sx={{ gap: 1.5, px: mini ? 1 : 2, justifyContent: mini ? 'center' : 'flex-start' }}>
        <Warehouse color="primary" />
        {!mini && (
          <Box>
            <Typography variant="subtitle1" fontWeight={800} lineHeight={1.1}>
              Estoque
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Gestão corporativa
            </Typography>
          </Box>
        )}
      </Toolbar>
      <Divider />
      <List sx={{ flex: 1, px: 1 }}>
        {mini
          ? leaves.map((leaf) => leafButton(leaf, true, false))
          : tree.map((entry) => {
              if (!isGroup(entry)) return leafButton(entry, false, false);
              const open = openGroups[entry.label] ?? false;
              const GroupIconCmp = entry.icon;
              return (
                <Box key={entry.label}>
                  <ListItemButton
                    onClick={() =>
                      setOpenGroups((prev) => ({ ...prev, [entry.label]: !open }))
                    }
                    sx={{ borderRadius: 2, mb: 0.5, px: 2 }}
                  >
                    <ListItemIcon sx={{ minWidth: 0, mr: 3, justifyContent: 'center' }}>
                      <GroupIconCmp />
                    </ListItemIcon>
                    <ListItemText
                      primary={entry.label}
                      primaryTypographyProps={{ fontWeight: 600, variant: 'body2' }}
                    />
                    {open ? <ExpandLess /> : <ExpandMore />}
                  </ListItemButton>
                  <Collapse in={open} timeout="auto" unmountOnExit>
                    {entry.children.map((child) => leafButton(child, false, true))}
                  </Collapse>
                </Box>
              );
            })}
      </List>
      <Divider />
      {mini ? (
        <Box sx={{ p: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
          <Tooltip title={user?.full_name ?? ''} placement="right">
            <Avatar
              onClick={() => navigate('/perfil')}
              sx={{ bgcolor: 'primary.main', width: 36, height: 36, cursor: 'pointer' }}
            >
              {user?.full_name?.[0]?.toUpperCase() ?? '?'}
            </Avatar>
          </Tooltip>
          <Tooltip title="Sair" placement="right">
            <IconButton onClick={() => void logout()} size="small">
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      ) : (
        <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36 }}>
            {user?.full_name?.[0]?.toUpperCase() ?? '?'}
          </Avatar>
          <Box
            sx={{ flex: 1, minWidth: 0, cursor: 'pointer' }}
            onClick={() => {
              navigate('/perfil');
              if (!isDesktop) setMobileOpen(false);
            }}
          >
            <Typography variant="body2" noWrap fontWeight={600}>
              {user?.full_name}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              {user?.role?.name}
            </Typography>
          </Box>
          <Tooltip title="Sair">
            <IconButton onClick={() => void logout()} size="small">
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        color="inherit"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          transition: widthTransition,
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            onClick={() => setMobileOpen((o) => !o)}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Tooltip title={collapsed ? 'Expandir menu' : 'Encolher menu'}>
            <IconButton
              onClick={toggleCollapsed}
              sx={{ mr: 2, display: { xs: 'none', md: 'inline-flex' } }}
            >
              {collapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
            </IconButton>
          </Tooltip>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            {leaves.find((i) => i.path === location.pathname)?.label ?? 'Sistema de Estoque'}
          </Typography>
          <Tooltip title={mode === 'dark' ? 'Modo claro' : 'Modo escuro'}>
            <IconButton onClick={toggleColorMode} color="inherit">
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 }, transition: widthTransition }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { width: DRAWER_WIDTH, ...HIDE_SCROLLBAR },
          }}
        >
          {renderDrawer(false)}
        </Drawer>
        <Drawer
          variant="permanent"
          open
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              borderRight: 1,
              borderColor: 'divider',
              overflowX: 'hidden',
              transition: widthTransition,
              ...HIDE_SCROLLBAR,
            },
          }}
        >
          {renderDrawer(collapsed)}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          p: { xs: 2, md: 3 },
          transition: widthTransition,
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
