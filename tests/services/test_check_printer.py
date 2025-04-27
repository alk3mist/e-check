from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from e_check.dto import Check, Payment, Product, User
from e_check.services.check_printer import CheckPrinter

CHECK_EXAMPLE = """\
      ФОП Джонсонюк Борис       

================================
3.00 х 298 870.00
Mavic 3T              896 610.00
--------------------------------

20.00 х 31 000.00
Дрон FPV з акумулятором 6S
чорний                620 000.00
================================

СУМА                1 516 610.00
Картка              1 516 610.00
Решта                       0.00
================================

        14.08.2023 14:42        
      Дякуємо за покупку!       \
"""

CHECK = Check(
    id=uuid4(),
    products=[
        Product(name="Mavic 3T", price=Decimal(298_870.00), quantity=Decimal(3.00)),
        Product(
            name="Дрон FPV з акумулятором 6S чорний",
            price=Decimal(31_000.00),
            quantity=Decimal(20.00),
        ),
    ],
    payment=Payment(
        amount=Decimal(1_516_610.00),
        type="cashless",
    ),
    created_at=datetime.strptime("14.08.2023 14:42", "%d.%m.%Y %H:%M"),
)
USER = User(username="john-boris", full_name="ФОП Джонсонюк Борис")


def test_check_print():
    printer = CheckPrinter(width=32)
    content = printer.render_check(USER, CHECK)
    assert content == CHECK_EXAMPLE
