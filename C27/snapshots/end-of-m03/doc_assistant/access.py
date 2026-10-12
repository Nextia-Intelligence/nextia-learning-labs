"""Who is asking, in which shop. Module 4 adds the roles and the membership check; until then the
practice user acts in every shop, with every access level (which is the problem Module 4 fixes)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    user_id: str
    name: str
    tenant_id: str
    shop: str            # the shop's name, for the prompt
    role: str

    @property
    def access_levels(self) -> tuple[str, ...]:
        return ("public", "staff")
