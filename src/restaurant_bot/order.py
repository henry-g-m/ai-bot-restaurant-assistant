from dataclasses import dataclass, field


@dataclass
class CartLine:
    name: str
    unit_price: float
    quantity: int


@dataclass
class Cart:
    items: list[CartLine] = field(default_factory=list)

    def add(self, name: str, unit_price: float, quantity: int) -> None:
        for line in self.items:
            if line.name == name:
                line.quantity += quantity
                return
        self.items.append(CartLine(name=name, unit_price=unit_price, quantity=quantity))

    def remove(self, name: str, quantity: int) -> None:
        for line in self.items:
            if line.name == name:
                line.quantity -= quantity
                if line.quantity <= 0:
                    self.items.remove(line)
                return

    def total(self) -> float:
        return sum(line.unit_price * line.quantity for line in self.items)

    def as_list(self) -> list[dict]:
        return [
            {"name": line.name, "unit_price": line.unit_price, "quantity": line.quantity}
            for line in self.items
        ]

    def clear(self) -> None:
        self.items.clear()


_sessions: dict[str, Cart] = {}


def get_or_create_cart(session_id: str) -> Cart:
    if session_id not in _sessions:
        _sessions[session_id] = Cart()
    return _sessions[session_id]
