import os
import time

import requests

from .models import Card, Inventory, PokemonSet, Wanted
from .serializers import CardSerializer

POKEMONTCG_BASE = 'https://api.pokemontcg.io/v2'
POKEMONTCG_API_KEY = os.environ.get('POKEMONTCG_API_KEY', '')


def _headers():
    return {'X-Api-Key': POKEMONTCG_API_KEY} if POKEMONTCG_API_KEY else {}


def _get(url, params=None, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=_headers(), timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
    raise last_error


def _set_to_dict(s):
    return {
        'id': s['id'],
        'name': s['name'],
        'series': s.get('series', ''),
        'release_date': s.get('releaseDate', ''),
        'total': s.get('total'),
        'logo_url': s.get('images', {}).get('logo', ''),
        'symbol_url': s.get('images', {}).get('symbol', ''),
    }


def _cache_sets(sets):
    for s in sets:
        PokemonSet.objects.update_or_create(
            api_id=s['id'],
            defaults={
                'name': s['name'],
                'series': s['series'],
                'release_date': s['release_date'],
                'total': s['total'],
                'logo_url': s['logo_url'],
                'symbol_url': s['symbol_url'],
            },
        )


def fetch_sets():
    try:
        data = _get(f'{POKEMONTCG_BASE}/sets', params={'orderBy': '-releaseDate', 'pageSize': 250})
        sets = [_set_to_dict(s) for s in data.get('data', [])]
        _cache_sets(sets)
        return sets
    except requests.RequestException:
        cached = PokemonSet.objects.order_by('-release_date')
        if cached.exists():
            return [
                {
                    'id': s.api_id,
                    'name': s.name,
                    'series': s.series,
                    'release_date': s.release_date,
                    'total': s.total,
                    'logo_url': s.logo_url,
                    'symbol_url': s.symbol_url,
                }
                for s in cached
            ]
        raise


def fetch_set_cards(set_id):
    data = _get(f'{POKEMONTCG_BASE}/cards', params={'q': f'set.id:{set_id}', 'pageSize': 250})
    cards = []
    for c in data.get('data', []):
        card, _ = Card.objects.update_or_create(
            api_id=c['id'],
            defaults=_api_card_to_db(c),
        )
        cards.append(CardSerializer(card).data)
    return cards


def search_cards(query, set_id='', page=1, page_size=20):
    terms = []
    if query:
        terms.append(f'name:{query}')
    if set_id:
        terms.append(f'set.id:{set_id}')
    q = ' '.join(terms)
    try:
        all_cards = []
        page_index = 1
        while True:
            data = _get(
                f'{POKEMONTCG_BASE}/cards',
                params={'q': q, 'page': page_index, 'pageSize': 250},
            )
            batch = data.get('data', [])
            total = data.get('totalCount', 0)
            for c in batch:
                card, _ = Card.objects.update_or_create(
                    api_id=c['id'],
                    defaults=_api_card_to_db(c),
                )
                all_cards.append(CardSerializer(card).data)
            if len(all_cards) >= total or not batch or len(all_cards) >= 500:
                break
            page_index += 1
        all_cards = all_cards[:500]
        return {
            'cards': all_cards,
            'count': len(all_cards),
            'total_count': len(all_cards),
            'page': 1,
            'page_size': len(all_cards) or 20,
        }
    except requests.RequestException:
        return search_cards_local(query, set_id, page, page_size)


def search_cards_local(query, set_id='', page=1, page_size=20):
    qs = Card.objects.all()
    if query:
        qs = qs.filter(name__icontains=query)
    if set_id:
        qs = qs.filter(set_id=set_id)
    qs = qs.order_by('name')
    total = qs.count()
    start = (page - 1) * page_size
    cards = [CardSerializer(c).data for c in qs[start:start + page_size]]
    return {
        'cards': cards,
        'count': len(cards),
        'total_count': total,
        'page': page,
        'page_size': page_size,
    }


def fetch_card(api_id):
    data = _get(f'{POKEMONTCG_BASE}/cards/{api_id}')
    return data['data']


def get_or_create_card(api_id, card_data=None):
    card = Card.objects.filter(api_id=api_id).first()
    if card is not None:
        return card
    if card_data is not None:
        return Card.objects.create(api_id=api_id, **_api_card_to_db(card_data))
    return Card.objects.create(api_id=api_id, **_api_card_to_db(fetch_card(api_id)))


def _api_card_to_db(c):
    if 'set' in c:
        return {
            'name': c['name'],
            'set_id': c['set']['id'],
            'set_name': c['set']['name'],
            'number': c.get('number', ''),
            'rarity': c.get('rarity', ''),
            'image_small': c.get('images', {}).get('small', ''),
            'image_large': c.get('images', {}).get('large', ''),
        }
    return {
        'name': c['name'],
        'set_id': c.get('set_id', ''),
        'set_name': c.get('set_name', ''),
        'number': c.get('number', ''),
        'rarity': c.get('rarity', ''),
        'image_small': c.get('image_small', ''),
        'image_large': c.get('image_large', ''),
    }


def apply_exchange(offer):
    """Move cards between users after both confirm an accepted offer.

    'offered' cards belong to the offerer and go to the recipient.
    'requested' cards belong to the recipient and go to the offerer.
    Fulfilled wanted entries are removed from each user's want list.
    """
    for oc in offer.cards.all():
        if oc.direction == 'offered':
            giver, receiver = offer.offerer, offer.recipient
        else:
            giver, receiver = offer.recipient, offer.offerer

        _remove_inventory(giver, oc.card, oc.quantity)
        _add_inventory(receiver, oc.card, oc.quantity)
        Wanted.objects.filter(user=receiver, card=oc.card).delete()


def _add_inventory(user, card, quantity):
    item, created = Inventory.objects.get_or_create(
        user=user, card=card, defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()


def _remove_inventory(user, card, quantity):
    item = Inventory.objects.filter(user=user, card=card).first()
    if item is None:
        return
    item.quantity -= quantity
    if item.quantity <= 0:
        item.delete()
    else:
        item.save()