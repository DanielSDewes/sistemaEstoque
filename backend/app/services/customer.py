"""Customer service - CRUD with nested address management."""
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.pagination import Page, PageParams
from app.models.customer import Customer, CustomerAddress
from app.models.enums import AuditAction
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.base import CrudService


class CustomerService(CrudService):
    model = Customer
    read_schema = CustomerRead
    entity_name = "Cliente"

    @staticmethod
    def _normalize_primary(addresses: list[dict]) -> None:
        """Ensure exactly one primary address when any address is provided."""
        if not addresses:
            return
        primaries = [a for a in addresses if a.get("is_primary")]
        if not primaries:
            addresses[0]["is_primary"] = True
        elif len(primaries) > 1:
            for extra in primaries[1:]:
                extra["is_primary"] = False

    def create(self, payload: CustomerCreate) -> CustomerRead:
        data = payload.model_dump()
        addresses = data.pop("addresses", []) or []
        self._normalize_primary(addresses)
        customer = Customer(
            **data, addresses=[CustomerAddress(**a) for a in addresses]
        )
        self.repo.add(customer)
        self.audit.log(
            AuditAction.CREATE,
            entity=self.entity_name,
            entity_id=customer.id,
            new_value=customer.name,
        )
        self.db.commit()
        self.db.refresh(customer)
        return self.read_schema.model_validate(customer)

    def update(self, obj_id: int, payload: CustomerUpdate) -> CustomerRead:
        customer = self.repo.get(obj_id)
        if not customer:
            raise NotFoundError(f"{self.entity_name} nao encontrado")
        data = payload.model_dump(exclude_unset=True)
        addresses = data.pop("addresses", None)
        before = {k: getattr(customer, k) for k in data}
        self.repo.update(customer, data)
        if addresses is not None:
            self._normalize_primary(addresses)
            # delete-orphan cascade removes the previous rows on reassignment.
            customer.addresses = [CustomerAddress(**a) for a in addresses]
        self.audit.log_diff(AuditAction.UPDATE, self.entity_name, customer.id, before, data)
        self.db.commit()
        self.db.refresh(customer)
        return self.read_schema.model_validate(customer)

    def delete(self, obj_id: int) -> None:
        customer = self.repo.get(obj_id)
        if not customer:
            raise NotFoundError(f"{self.entity_name} nao encontrado")
        if customer.orders:
            raise BusinessRuleError(
                "Nao e possivel excluir clientes com pedidos. Inative o cliente."
            )
        self.audit.log(
            AuditAction.DELETE,
            entity=self.entity_name,
            entity_id=customer.id,
            old_value=customer.name,
        )
        self.repo.delete(customer)
        self.db.commit()

    def search(self, params: PageParams, term: str | None) -> Page[CustomerRead]:
        stmt = CustomerRepository(self.db).search(term)
        return self.list(params, stmt)
