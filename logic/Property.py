class Property:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name")
        self.type = data.get("type")
        self.group = data.get("group")
        self.price = data.get("price")
        self.location = data.get("location")
        self.rent = data.get("rent", [])
        self.rent_multiplier = data.get("rentMultiplier", [])
        self.mortgage = data.get("mortgage")
        self.house_cost = data.get("houseCost")
        self.hotel_cost = data.get("hotelCost")

        self.house_count = 0
        self.hotel_count = 0
        self.owner = None
        self.is_mortgaged = False

    def get_current_rent(self):
        if self.type == "utility":
            return 0

        if self.type == "railroad":
            return self.rent[0]

        if self.hotel_count > 0:
            return self.rent[5]
        else:
            return self.rent[self.house_count]

    def get_current_rent(self, dice_roll=0, group_owned_count=1, has_monopoly=False, chance_multiplier=1):
        if self.is_mortgaged:
            return 0

        if self.type == "utility":
            base_multiplier = self.rent_multiplier[1] if group_owned_count == 2 else self.rent_multiplier[0]
            final_multiplier = chance_multiplier if chance_multiplier > 1 else base_multiplier
            return dice_roll * final_multiplier

        if self.type == "railroad":
            base_rent = self.rent[group_owned_count - 1]
            return base_rent * chance_multiplier

        if self.house_count == 0 and self.hotel_count == 0:
            return self.rent[0] * 2 if has_monopoly else self.rent[0]
        elif self.hotel_count > 0:
            return self.rent[5]
        else:
            return self.rent[self.house_count]