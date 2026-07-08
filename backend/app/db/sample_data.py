"""Optional demo data seeder: catalogs, locations, products and movements.

Run with:  python -m app.db.sample_data
Idempotent-ish: it skips seeding when products already exist.
"""
import logging
import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.catalog import Brand, Category, Group
from app.models.customer import Customer, CustomerAddress
from app.models.enums import (
    FinancialCategoryKind,
    FinancialDirection,
    MovementDirection,
    MovementType,
    OrderStatus,
)
from app.models.finance import BankAccount, CostCenter, FinancialCategory, PaymentMethod
from app.models.location import Corridor, ProductLocation, Shelf
from app.models.movement import StockMovement
from app.models.order import Order, OrderItem
from app.models.product import Batch, Product
from app.models.supplier import ProductSupplier, Supplier
from app.schemas.finance import (
    FinancialAccountCreate,
    InstallmentInput,
    InstallmentPlan,
    SettlementCreate,
)
from app.services.finance import FinanceService

logger = logging.getLogger("app.sample")


def seed_sample_data(db: Session) -> None:
    if db.execute(select(Product.id).limit(1)).first():
        logger.info("Sample data skipped (products already exist).")
        return

    categories = {
        name: Category(code=name[:3].upper(), name=name)
        for name in ["Bebidas", "Ferramentas", "Alimentos", "Eletronicos"]
    }
    groups = {
        name: Group(code=name[:3].upper(), name=name)
        for name in ["Refrigerantes", "Cervejas", "Manuais", "Perecíveis", "Audio"]
    }
    brands = {
        name: Brand(code=f"MRC{i}", name=name)
        for i, name in enumerate(["Marca A", "Marca B", "Marca C"], start=1)
    }
    db.add_all([*categories.values(), *groups.values(), *brands.values()])
    db.flush()

    corridors = [Corridor(code=f"COR-{c}", name=f"Corredor {c}") for c in ["A", "B", "C"]]
    db.add_all(corridors)
    db.flush()
    shelves = []
    for cor in corridors:
        for n in range(1, 4):
            shelves.append(Shelf(code=f"{cor.code}-P{n:02d}", name=f"Prateleira {n:02d}", corridor_id=cor.id, capacity=100))
    db.add_all(shelves)
    db.flush()

    suppliers = [
        Supplier(legal_name="Distribuidora Alpha LTDA", trade_name="Alpha", cnpj="11111111000191", city="Sao Paulo", state="SP"),
        Supplier(legal_name="Beta Comercio LTDA", trade_name="Beta", cnpj="22222222000172", city="Campinas", state="SP"),
    ]
    db.add_all(suppliers)
    db.flush()

    demo = [
        ("Refrigerante Cola 2L", "Bebidas", "Refrigerantes", 5.5),
        ("Cerveja Pilsen 350ml", "Bebidas", "Cervejas", 3.2),
        ("Furadeira 500W", "Ferramentas", "Manuais", 220.0),
        ("Martelo Aco", "Ferramentas", "Manuais", 35.0),
        ("Arroz 5kg", "Alimentos", "Perecíveis", 24.9),
        ("Fone Bluetooth", "Eletronicos", "Audio", 89.9),
    ]
    products: list[Product] = []
    for i, (name, cat, grp, _cost) in enumerate(demo, start=1):
        p = Product(
            internal_code=f"SKU{i:04d}",
            barcode=f"789000000{i:04d}",
            sku=f"SKU{i:04d}",
            name=name,
            category_id=categories[cat].id,
            group_id=groups[grp].id,
            brand_id=random.choice(list(brands.values())).id,
            unit="UN",
            min_stock=20,
            max_stock=500,
            reorder_point=40,
            sale_price=round(_cost * 1.6, 2),  # demo markup over cost
        )
        products.append(p)
    db.add_all(products)
    db.flush()

    # Locations, batches, suppliers and an initial purchase per product.
    for idx, p in enumerate(products):
        shelf = shelves[idx % len(shelves)]
        db.add(ProductLocation(product_id=p.id, corridor_id=shelf.corridor_id, shelf_id=shelf.id, quantity=0, is_primary=True))
        db.add(Batch(product_id=p.id, lot_number=f"L{p.internal_code}", manufacture_date=date.today() - timedelta(days=30), expiry_date=date.today() + timedelta(days=random.choice([20, 45, 120, 300]))))
        db.add(ProductSupplier(product_id=p.id, supplier_id=suppliers[idx % 2].id, current_price=demo[idx][3], last_price=demo[idx][3], average_price=demo[idx][3], is_primary=True))

    db.flush()

    # Movements over the last 14 days to populate charts.
    now = datetime.now(UTC)
    for p in products:
        opening = random.randint(80, 200)
        cost = next(c for n, _, _, c in demo if n == p.name)
        # Seed the weighted-average cost directly (movements are inserted in bulk
        # here rather than through MovementService, which maintains it live).
        p.average_cost = cost
        db.add(StockMovement(product_id=p.id, movement_type=MovementType.PURCHASE, direction=MovementDirection.IN, quantity=opening, unit_cost=cost, moved_at=now - timedelta(days=14)))
        for d in range(13, 0, -1):
            if random.random() < 0.6:
                out = random.randint(1, 12)
                db.add(StockMovement(product_id=p.id, movement_type=MovementType.SALE, direction=MovementDirection.OUT, quantity=out, moved_at=now - timedelta(days=d)))

    # --- CRM demo: customers (with addresses) and a couple of orders ---
    customers = [
        Customer(
            name="Maria Souza", phone="(11) 98888-1111",
            document="123.456.789-00", email="maria@example.com",
            addresses=[
                CustomerAddress(label="Casa", street="Rua das Flores", number="100", district="Centro", city="Sao Paulo", state="SP", zip_code="01000-000", is_primary=True),
                CustomerAddress(label="Trabalho", street="Av. Paulista", number="900", district="Bela Vista", city="Sao Paulo", state="SP", zip_code="01310-000"),
            ],
        ),
        Customer(
            name="Joao Pereira", phone="(21) 97777-2222", document="987.654.321-00",
            addresses=[CustomerAddress(label="Casa", street="Rua do Sol", number="45", city="Rio de Janeiro", state="RJ", zip_code="20000-000", is_primary=True)],
        ),
        Customer(name="Ana Lima", phone="(31) 96666-3333"),
    ]
    db.add_all(customers)
    db.flush()

    # One confirmed order (deducts stock via SALE movements) + one draft.
    confirmed = Order(customer_id=customers[0].id, status=OrderStatus.CONFIRMED, order_date=now, confirmed_at=now, extra_cost=15.0, notes="Pedido de demonstracao (frete incluso)")
    for prod, qty, price in [(products[0], 3, 7.5), (products[5], 1, 129.9)]:
        mv = StockMovement(product_id=prod.id, movement_type=MovementType.SALE, direction=MovementDirection.OUT, quantity=qty, moved_at=now, reason="Pedido demo")
        db.add(mv)
        db.flush()
        confirmed.items.append(OrderItem(product_id=prod.id, quantity=qty, unit_price=price, line_total=qty * price, unit_cost=prod.average_cost, movement_id=mv.id))
    confirmed.total_amount = sum(i.line_total for i in confirmed.items)
    db.add(confirmed)
    db.flush()
    confirmed.number = f"PED-{confirmed.id:06d}"

    draft = Order(customer_id=customers[1].id, status=OrderStatus.DRAFT, order_date=now)
    draft.items.append(OrderItem(product_id=products[2].id, quantity=1, unit_price=250.0, line_total=250.0))
    draft.total_amount = 250.0
    db.add(draft)
    db.flush()
    draft.number = f"PED-{draft.id:06d}"
    db.commit()

    # --- Finance demo: registrations, one receivable (partly settled) + one payable ---
    pix = PaymentMethod(name="PIX")
    boleto = PaymentMethod(name="Boleto")
    cat_sale = FinancialCategory(name="Vendas", kind=FinancialCategoryKind.INCOME)
    cat_supplier = FinancialCategory(name="Fornecedores", kind=FinancialCategoryKind.EXPENSE)
    cc_com = CostCenter(name="Comercial")
    bank = BankAccount(name="Caixa", opening_balance=1000, current_balance=1000)
    db.add_all([pix, boleto, cat_sale, cat_supplier, cc_com, bank])
    db.commit()

    fin = FinanceService(db)
    today = date.today()
    receivable = fin.create_account(
        FinancialAccountCreate(
            direction=FinancialDirection.RECEIVABLE,
            customer_id=customers[0].id,
            document="FAT-00125",
            description="Venda a prazo",
            category_id=cat_sale.id,
            cost_center_id=cc_com.id,
            total_amount=850,
            installment_plan=InstallmentPlan(
                count=2, first_due_date=today + timedelta(days=15), interval_days=30
            ),
        )
    )
    # Settle the first installment fully, crediting the bank account.
    first = receivable.installments[0]
    fin.settle(
        first.id,
        SettlementCreate(amount=first.balance, payment_method_id=pix.id, bank_account_id=bank.id),
    )

    fin.create_account(
        FinancialAccountCreate(
            direction=FinancialDirection.PAYABLE,
            supplier_id=suppliers[0].id,
            document="NF 4521",
            description="Compra de mercadorias",
            category_id=cat_supplier.id,
            installments=[InstallmentInput(due_date=today - timedelta(days=3), amount=2800)],
        )
    )

    db.commit()
    logger.info("Sample data seeded: %d products, %d customers.", len(products), len(customers))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as session:
        seed_sample_data(session)
