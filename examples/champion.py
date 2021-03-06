import cassiopeia as cass
from cassiopeia import Champion


def get_champions():
    # annie = Champion(name="Annie", region="NA")
    annie = Champion(name="Annie")
    print(annie.name)
    print(annie.title)
    for spell in annie.spells:
        print(spell.name, spell.keywords)

    print(annie.info.difficulty)
    print(annie.passive.name)
    print({item.name: count for item, count in annie.recommended_itemsets[0].item_sets[0].items.items()})
    print(annie.free_to_play)
    print(annie._Ghost__all_loaded)
    print(annie)

    # ziggs = cass.get_champion(region="NA", "Ziggs")
    ziggs = cass.get_champion("Ziggs")
    print(ziggs.name)
    print(ziggs.region)
    print({item.name: count for item, count in ziggs.recommended_itemsets[0].item_sets[0].items.items()})
    print(ziggs.free_to_play)
    for spell in ziggs.spells:
        for var in spell.variables:
            print(spell.name, var)
    print(ziggs._Ghost__all_loaded)


if __name__ == "__main__":
    get_champions()
