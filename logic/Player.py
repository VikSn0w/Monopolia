from logic.Property import Property


class Player:
    def __init__(self, name, money=1500):
        self.name = name
        self.money = money
        self.owned_properties: list[Property] = []
        self.location = 0
        self.is_in_jail = False
        self.turns_in_jail = 0          # FIX: was missing; GameManager.send_to_jail writes it
        self.goojf_cards = []

    def buy_property(self, property_obj: Property):
        self.money -= property_obj.price
        property_obj.owner = self
        self.owned_properties.append(property_obj)

    def get_property(self, location: int) -> Property:
        for prop in self.owned_properties:
            if prop.location == location:
                return prop
        raise ValueError(f"Player does not own property at location {location}")

    def get_effective_houses(self, prop: Property) -> int:
        return 5 if prop.hotel_count > 0 else prop.house_count

    def buy_house(self, location: int):
        prop = self.get_property(location)
        if self.can_build_house(location, self.get_owned_group_count(prop.group)):
            self.money -= prop.house_cost
            prop.house_count += 1

    def can_sell_house(self, location: int) -> bool:
        prop = self.get_property(location)
        if prop.house_count == 0 and prop.hotel_count == 0:
            return False

        my_houses = self.get_effective_houses(prop)
        group_props = [p for p in self.owned_properties if p.group == prop.group]
        for p in group_props:
            if self.get_effective_houses(p) > my_houses:
                print(f"Cannot sell building on {prop.name} due to even sell rule. Sell on {p.name} first.")
                return False
        return True

    def sell_house(self, location: int):
        if self.can_sell_house(location):
            prop = self.get_property(location)
            if prop.hotel_count > 0:
                prop.hotel_count -= 1
                prop.house_count = 4
                self.money += (prop.hotel_cost / 2)
            else:
                self.money += (prop.house_cost / 2)
                prop.house_count -= 1

    def buy_hotel(self, location: int):
        prop = self.get_property(location)
        group_props = [p for p in self.owned_properties if p.group == prop.group]
        for p in group_props:
            if self.get_effective_houses(p) < 4:
                print(f"Cannot build hotel on {prop.name}. {p.name} needs more houses.")
                return

        if prop.hotel_count > 0:
            print(f"{prop.name} already has a hotel.")
            return

        self.money -= prop.hotel_cost
        prop.hotel_count += 1
        prop.house_count = 0

    def sell_hotel(self, location: int, bank_houses_left: int):
        if self.can_sell_house(location):
            prop = self.get_property(location)
            if prop.hotel_count == 0:
                return

            self.money += (prop.hotel_cost / 2)
            prop.hotel_count -= 1

            houses_to_place = min(4, bank_houses_left)
            prop.house_count = houses_to_place

    def mortgage_property(self, location: int):
        prop = self.get_property(location)
        group_props = [p for p in self.owned_properties if p.group == prop.group]
        for p in group_props:
            if p.house_count > 0 or p.hotel_count > 0:
                print(f"Cannot mortgage {prop.name}. Must sell all buildings in the {prop.group} group first.")
                return

        self.money += prop.mortgage
        prop.is_mortgaged = True

    def unmortgage_property(self, location: int):
        prop = self.get_property(location)
        cost = prop.mortgage + (prop.mortgage * 0.10)
        self.money -= cost
        prop.is_mortgaged = False

    def get_owned_group_count(self, group: str) -> int:
        return sum(1 for p in self.owned_properties if p.group == group)

    def get_owned_type_count(self, prop_type: str) -> int:
        return sum(1 for p in self.owned_properties if p.type == prop_type)

    def can_build_house(self, location: int, total_in_group: int) -> bool:
        prop = self.get_property(location)
        owns_all_colors = self.get_owned_group_count(prop.group) == total_in_group

        if not owns_all_colors:
            print(f"{self.name} cannot build on {prop.name}. You need the full {prop.group} set!")
            return False
        if prop.hotel_count > 0 or prop.house_count >= 4:
            print(f"{prop.name} already has maximum houses or a hotel.")
            return False

        my_houses = self.get_effective_houses(prop)
        group_props = [p for p in self.owned_properties if p.group == prop.group]
        for p in group_props:
            if self.get_effective_houses(p) < my_houses:
                print(f"Cannot build on {prop.name} due to even build rule. Build on {p.name} first.")
                return False
        return True