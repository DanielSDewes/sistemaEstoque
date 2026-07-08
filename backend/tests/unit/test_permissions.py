"""Unit tests for the permission catalog and default role mapping."""
from app.core.permissions import DEFAULT_ROLES, READ_ONLY, all_permissions


def test_all_permissions_include_crud_and_special():
    perms = all_permissions()
    assert "product:create" in perms
    assert "inventory:approve" in perms
    assert "movement:create" in perms


def test_default_roles_present():
    assert set(DEFAULT_ROLES) == {
        "Administrador",
        "Supervisor",
        "Operador",
        "Somente Consulta",
    }


def test_read_only_has_no_write_permissions():
    assert all(code.endswith(":view") or code.startswith(("dashboard", "report")) for code in READ_ONLY)
    assert "product:create" not in READ_ONLY
