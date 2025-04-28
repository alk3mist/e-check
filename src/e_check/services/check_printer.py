import re
from dataclasses import dataclass
from decimal import Decimal

from e_check.dto import Check, Product, User


@dataclass
class CheckPrinter:
    width: int = 32

    def render_check(self, user: User, check: Check) -> str:
        content = ""
        content += f"{user.full_name:^{self.width}}\n"
        content += "\n"
        content += f"{'':=^{self.width}}\n"

        for i, product in enumerate(check.products, start=1):
            content += self.render_product(product)
            if i != len(check.products):
                content += "-" * self.width
            else:
                content += "=" * self.width
            content += "\n\n"

        content += _expand("СУМА", f"{_df(check.total)}", self.width)
        content += "\n"

        payment = "Картка" if check.payment.type == "cashless" else "Готівка"
        content += _expand(payment, f"{_df(check.payment.amount)}", self.width)
        content += "\n"

        content += _expand("Решта", f"{_df(check.rest)}", self.width)
        content += "\n"

        content += "=" * self.width
        content += "\n\n"

        date = f"{check.created_at:%d.%m.%Y %H:%M}"
        content += f"{date:^{self.width}}\n"

        content += f"{'Дякуємо за покупку!':^{self.width}}"
        return content

    def render_product(self, product: Product) -> str:
        content = f"{_df(product.quantity)} х {_df(product.price)}\n"

        lines = _split_lines(product.name, self.width)
        if len(lines) == 1:
            try:
                content += _expand(lines[0], _df(product.total), self.width)
            except ValueError:
                content += lines[0]
                content += "\n"
                content += _expand("", _df(product.total), self.width)
        else:
            for line in lines[:-1]:
                content += f"{line}\n"
            try:
                content += _expand(lines[-1], _df(product.total), self.width)
            except ValueError:
                content += lines[-1]
                content += "\n"
                content += _expand("", _df(product.total), self.width)

        content += "\n"
        return content


def _df(v: Decimal) -> str:
    """Format decimal value"""
    return f"{v:,.2f}".replace(",", " ")


def _expand(a: str, b: str, width: int) -> str:
    ab_length = len(a) + len(b)
    if ab_length >= width:
        raise ValueError("Arguments length is too big")
    spaces = (width - ab_length) * " "
    return f"{a}{spaces}{b}"


def _split_lines(s: str, width: int) -> list[str]:
    words = _split_words(s, width)
    lines: list[str] = []
    line = ""
    for word in words:
        if (len(line) + 1 + len(word)) > width:
            lines.append(line)
            line = word
            continue

        if len(line) == 0:
            line = word
        else:
            line += f" {word}"

    lines.append(line)
    return lines


def _split_words(s: str, width: int) -> list[str]:
    words = re.split(r"\s+", s)
    cut_words: list[str] = []
    for word in words:
        if len(word) <= width:
            cut_words.append(word)
            continue
        word_parts: list[str] = []
        while len(word) > width:
            part = word[:width]
            word_parts.append(part)
            word = word[width:]
        cut_words.extend(word_parts)
        cut_words.append(word)
    return cut_words
