from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from api.models import Card, Inventory, Offer, OfferCard, PokemonSet, UserProfile, Wanted
from api.services import fetch_card

PASSWORD = 'test123'

USERS = [
    {'username': 'stefano', 'password': PASSWORD, 'location': 'Las Condes'},
    {'username': 'mario', 'password': PASSWORD, 'location': 'Providencia'},
    {'username': 'figue', 'password': PASSWORD, 'location': 'Santiago Centro'},
]

CARD_POOL = [
    # Base Set
    {'api_id': 'base1-4', 'name': 'Charizard', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '4', 'rarity': 'Rare Holo'},
    {'api_id': 'base1-58', 'name': 'Pikachu', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '58', 'rarity': 'Common'},
    {'api_id': 'base1-2', 'name': 'Blastoise', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '2', 'rarity': 'Rare Holo'},
    {'api_id': 'base1-3', 'name': 'Venusaur', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '3', 'rarity': 'Rare Holo'},
    {'api_id': 'base1-6', 'name': 'Alakazam', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '6', 'rarity': 'Rare Holo'},
    {'api_id': 'base1-8', 'name': 'Gyarados', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '8', 'rarity': 'Rare Holo'},
    {'api_id': 'base1-12', 'name': 'Mewtwo', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '12', 'rarity': 'Rare Holo'},
    {'api_id': 'base1-16', 'name': 'Raichu', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '16', 'rarity': 'Rare Holo'},
    {'api_id': 'base1-88', 'name': 'Growlithe', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '88', 'rarity': 'Common'},
    {'api_id': 'base1-63', 'name': 'Squirtle', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '63', 'rarity': 'Common'},
    {'api_id': 'base1-77', 'name': 'Bulbasaur', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '77', 'rarity': 'Common'},
    {'api_id': 'base1-38', 'name': 'Eevee', 'set_id': 'base1', 'set_name': 'Base Set', 'number': '38', 'rarity': 'Common'},
    # Modern era (Scarlet & Violet)
    {'api_id': 'sv2-63', 'name': 'Pikachu ex', 'set_id': 'sv2', 'set_name': 'Paldea Evolved', 'number': '63', 'rarity': 'Double Rare'},
    {'api_id': 'sv8-57', 'name': 'Pikachu ex', 'set_id': 'sv8', 'set_name': 'Surging Sparks', 'number': '57', 'rarity': 'Double Rare'},
    {'api_id': 'me2pt5-276', 'name': 'Pikachu ex', 'set_id': 'me2pt5', 'set_name': 'Ascended Heroes', 'number': '276', 'rarity': 'Illustration Rare'},
    {'api_id': 'sv3pt5-206', 'name': 'Charizard ex', 'set_id': 'sv3pt5', 'set_name': '151', 'number': '206', 'rarity': 'Illustration Rare'},
    {'api_id': 'sv3pt5-199', 'name': 'Charizard ex', 'set_id': 'sv3pt5', 'set_name': '151', 'number': '199', 'rarity': 'Ultra Rare'},
    {'api_id': 'sv3pt5-12', 'name': 'Charmander', 'set_id': 'sv3pt5', 'set_name': '151', 'number': '12', 'rarity': 'Common'},
    {'api_id': 'sv3pt5-6', 'name': 'Bulbasaur', 'set_id': 'sv3pt5', 'set_name': '151', 'number': '6', 'rarity': 'Common'},
    {'api_id': 'sv1-25', 'name': 'Pikachu', 'set_id': 'sv1', 'set_name': 'Scarlet & Violet', 'number': '25', 'rarity': 'Common'},
    {'api_id': 'sv1-198', 'name': 'Miraidon ex', 'set_id': 'sv1', 'set_name': 'Scarlet & Violet', 'number': '198', 'rarity': 'Ultra Rare'},
    {'api_id': 'sv1-199', 'name': 'Koraidon ex', 'set_id': 'sv1', 'set_name': 'Scarlet & Violet', 'number': '199', 'rarity': 'Ultra Rare'},
    {'api_id': 'sv3-182', 'name': 'Gardevoir ex', 'set_id': 'sv3', 'set_name': 'Obsidian Flames', 'number': '182', 'rarity': 'Double Rare'},
    {'api_id': 'sv4-45', 'name': 'Charizard ex', 'set_id': 'sv4', 'set_name': 'Paradox Rift', 'number': '45', 'rarity': 'Double Rare'},
    {'api_id': 'sv4pt5-91', 'name': 'Eevee', 'set_id': 'sv4pt5', 'set_name': 'Paldean Fates', 'number': '91', 'rarity': 'Illustration Rare'},
    {'api_id': 'sv5-30', 'name': 'Charizard ex', 'set_id': 'sv5', 'set_name': 'Temporal Forces', 'number': '30', 'rarity': 'Double Rare'},
    {'api_id': 'sv7-125', 'name': 'Mew ex', 'set_id': 'sv7', 'set_name': 'Stellar Crown', 'number': '125', 'rarity': 'Double Rare'},
    # Sword & Shield era
    {'api_id': 'swsh1-149', 'name': 'Zapdos V', 'set_id': 'swsh1', 'set_name': 'Sword & Shield', 'number': '149', 'rarity': 'Rare Holo V'},
    {'api_id': 'swsh12-165', 'name': 'Charizard VSTAR', 'set_id': 'swsh12', 'set_name': 'Silver Tempest', 'number': '165', 'rarity': 'Rare Holo VSTAR'},
    {'api_id': 'swsh4-25', 'name': 'Charizard', 'set_id': 'swsh4', 'set_name': 'Vivid Voltage', 'number': '25', 'rarity': 'Rare'},
    {'api_id': 'swsh7-117', 'name': 'Gengar', 'set_id': 'swsh7', 'set_name': 'Evolving Skies', 'number': '117', 'rarity': 'Rare'},
    {'api_id': 'swsh7-133', 'name': 'Umbreon V', 'set_id': 'swsh7', 'set_name': 'Evolving Skies', 'number': '133', 'rarity': 'Rare Holo V'},
    {'api_id': 'swsh9-157', 'name': 'Hisuian Zoroark VSTAR', 'set_id': 'swsh9', 'set_name': 'Brilliant Stars', 'number': '157', 'rarity': 'Rare Holo VSTAR'},
    # Sun & Moon era
    {'api_id': 'sm1-149', 'name': 'Tapu Lele GX', 'set_id': 'sm1', 'set_name': 'Sun & Moon', 'number': '149', 'rarity': 'Rare Holo GX'},
    {'api_id': 'sm12-135', 'name': 'Dedenne GX', 'set_id': 'sm12', 'set_name': 'Cosmic Eclipse', 'number': '135', 'rarity': 'Rare Holo GX'},
    {'api_id': 'sm8-159', 'name': 'Mewtwo GX', 'set_id': 'sm8', 'set_name': 'Lost Thunder', 'number': '159', 'rarity': 'Rare Holo GX'},
    # XY era
    {'api_id': 'xy1-108', 'name': 'Charizard EX', 'set_id': 'xy1', 'set_name': 'XY', 'number': '108', 'rarity': 'Rare Holo EX'},
    {'api_id': 'xy2-21', 'name': 'Blastoise EX', 'set_id': 'xy2', 'set_name': 'Flashfire', 'number': '21', 'rarity': 'Rare Holo EX'},
]

SEED_POOL = {
    'stefano': [
        {'api_id': 'base1-4', 'inventory': 8, 'wanted': 0},
        {'api_id': 'base1-58', 'inventory': 10, 'wanted': 0},
        {'api_id': 'base1-8', 'inventory': 4, 'wanted': 0},
        {'api_id': 'base1-12', 'inventory': 3, 'wanted': 0},
        {'api_id': 'base1-38', 'inventory': 6, 'wanted': 0},
        {'api_id': 'sv8-57', 'inventory': 5, 'wanted': 0},
        {'api_id': 'sv3pt5-206', 'inventory': 3, 'wanted': 0},
        {'api_id': 'sv1-198', 'inventory': 3, 'wanted': 0},
        {'api_id': 'swsh12-165', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sm8-159', 'inventory': 4, 'wanted': 0},
        {'api_id': 'xy1-108', 'inventory': 3, 'wanted': 0},
        {'api_id': 'sv3pt5-199', 'inventory': 3, 'wanted': 0},
        {'api_id': 'me2pt5-276', 'inventory': 0, 'wanted': 2},
        {'api_id': 'base1-2', 'inventory': 0, 'wanted': 1},
        {'api_id': 'sv7-125', 'inventory': 0, 'wanted': 1},
        {'api_id': 'swsh7-133', 'inventory': 0, 'wanted': 1},
    ],
    'mario': [
        {'api_id': 'base1-58', 'inventory': 15, 'wanted': 0},
        {'api_id': 'base1-3', 'inventory': 4, 'wanted': 0},
        {'api_id': 'base1-6', 'inventory': 4, 'wanted': 0},
        {'api_id': 'base1-16', 'inventory': 5, 'wanted': 0},
        {'api_id': 'base1-63', 'inventory': 8, 'wanted': 0},
        {'api_id': 'base1-77', 'inventory': 8, 'wanted': 0},
        {'api_id': 'sv2-63', 'inventory': 6, 'wanted': 0},
        {'api_id': 'me2pt5-276', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sv3-182', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sv5-30', 'inventory': 3, 'wanted': 0},
        {'api_id': 'swsh4-25', 'inventory': 5, 'wanted': 0},
        {'api_id': 'swsh9-157', 'inventory': 3, 'wanted': 0},
        {'api_id': 'sm1-149', 'inventory': 4, 'wanted': 0},
        {'api_id': 'xy2-21', 'inventory': 3, 'wanted': 0},
        {'api_id': 'base1-4', 'inventory': 0, 'wanted': 1},
        {'api_id': 'sv8-57', 'inventory': 0, 'wanted': 1},
        {'api_id': 'sv3pt5-12', 'inventory': 0, 'wanted': 1},
    ],
    'figue': [
        {'api_id': 'sv3pt5-206', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sv3pt5-6', 'inventory': 6, 'wanted': 0},
        {'api_id': 'sv4-45', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sv4pt5-91', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sv7-125', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sv1-199', 'inventory': 3, 'wanted': 0},
        {'api_id': 'base1-88', 'inventory': 5, 'wanted': 0},
        {'api_id': 'swsh7-117', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sm12-135', 'inventory': 4, 'wanted': 0},
        {'api_id': 'sv3pt5-12', 'inventory': 3, 'wanted': 0},
        {'api_id': 'base1-2', 'inventory': 0, 'wanted': 1},
        {'api_id': 'me2pt5-276', 'inventory': 0, 'wanted': 1},
        {'api_id': 'sv1-198', 'inventory': 0, 'wanted': 1},
        {'api_id': 'swsh12-165', 'inventory': 0, 'wanted': 1},
    ],
}


class Command(BaseCommand):
    help = 'Seed the database with test users, cards, inventory, want lists and a sample offer.'

    def handle(self, *args, **options):
        users = {}
        for data in USERS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={'password': '', 'is_active': True},
            )
            user.set_password(data['password'])
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.location = data['location']
            profile.save()
            users[data['username']] = user
            self.stdout.write(self.style.SUCCESS(f"user {data['username']} ({'created' if created else 'updated'})"))

        cards = {}
        for c in CARD_POOL:
            card = self._ensure_card(c)
            cards[c['api_id']] = card
            PokemonSet.objects.update_or_create(
                api_id=c['set_id'],
                defaults={'name': c['set_name'], 'series': '', 'total': None},
            )

        self.stdout.write(f"cached {len(cards)} cards")

        for username, rows in SEED_POOL.items():
            user = users[username]
            Inventory.objects.filter(user=user).delete()
            Wanted.objects.filter(user=user).delete()
            for row in rows:
                card = cards[row['api_id']]
                if row['inventory']:
                    Inventory.objects.update_or_create(
                        user=user, card=card, defaults={'quantity': row['inventory']}
                    )
                if row['wanted']:
                    Wanted.objects.update_or_create(
                        user=user, card=card, defaults={'quantity': row['wanted']}
                    )
            self.stdout.write(self.style.SUCCESS(
                f"{username}: {Inventory.objects.filter(user=user).count()} inventory, "
                f"{Wanted.objects.filter(user=user).count()} wanted"
            ))

        self._seed_offer(users)

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))

    def _ensure_card(self, c):
        card = Card.objects.filter(api_id=c['api_id']).first()
        if card is not None:
            if not card.image_large:
                try:
                    data = fetch_card(c['api_id'])
                    card.name = data['name']
                    card.set_id = data['set']['id']
                    card.set_name = data['set']['name']
                    card.number = data.get('number', '')
                    card.rarity = data.get('rarity', '')
                    card.image_small = data.get('images', {}).get('small', '')
                    card.image_large = data.get('images', {}).get('large', '')
                    card.save()
                except Exception:
                    pass
            return card
        try:
            data = fetch_card(c['api_id'])
            return Card.objects.create(
                api_id=data['id'],
                name=data['name'],
                set_id=data['set']['id'],
                set_name=data['set']['name'],
                number=data.get('number', ''),
                rarity=data.get('rarity', ''),
                image_small=data.get('images', {}).get('small', ''),
                image_large=data.get('images', {}).get('large', ''),
            )
        except Exception:
            return Card.objects.create(
                api_id=c['api_id'],
                name=c['name'],
                set_id=c['set_id'],
                set_name=c['set_name'],
                number=c['number'],
                rarity=c['rarity'],
            )

    def _seed_offer(self, users):
        Offer.objects.all().delete()
        OfferCard.objects.all().delete()

        mario = users['mario']
        stefano = users['stefano']

        offer = Offer.objects.create(
            offerer=mario,
            recipient=stefano,
            status='pending',
            message='Hi! Would you trade my Pikachu ex for your Charizard?',
        )
        OfferCard.objects.create(
            offer=offer,
            card=Card.objects.get(api_id='me2pt5-276'),
            direction='offered',
            quantity=1,
        )
        OfferCard.objects.create(
            offer=offer,
            card=Card.objects.get(api_id='base1-4'),
            direction='requested',
            quantity=1,
        )
        self.stdout.write(self.style.SUCCESS('seeded 1 sample offer'))