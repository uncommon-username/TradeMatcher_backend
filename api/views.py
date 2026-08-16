from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.http import JsonResponse
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Inventory, Offer, OfferCard, Wanted
from .places import SANTIAGO_PLACES
from .services import apply_exchange
from .serializers import (
    InventorySerializer,
    OfferSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
    WantedSerializer,
)
from . import services


def parse_card_quantities(raw):
    """Normalize card selections into [(card_id, quantity)] pairs.

    Accepts a list of ids ([1, 2]) or a list of dicts ([{'card_id': 1, 'quantity': 2}]).
    """
    result = []
    for item in raw or []:
        if isinstance(item, dict):
            card_id = item.get('card_id')
            quantity = int(item.get('quantity', 1))
        else:
            card_id = item
            quantity = 1
        if card_id is not None and quantity > 0:
            result.append((card_id, quantity))
    return result


def _has_cards(user, selections):
    """Check the user owns enough of each card in selections."""
    for card_id, quantity in selections:
        owned = Inventory.objects.filter(user=user, card_id=card_id).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        if owned < quantity:
            return False
    return True


def health_check(request):
    return JsonResponse({'status': 'ok'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = User.objects.filter(username=username).first()
    if user is None or not user.check_password(password):
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UserSerializer(user).data})


@api_view(['POST'])
def logout(request):
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'PATCH'])
def profile(request):
    profile = request.user.profile
    if request.method == 'PATCH':
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    return Response(ProfileSerializer(profile).data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def places(request):
    return Response({'places': SANTIAGO_PLACES})


@api_view(['GET'])
def sets(request):
    try:
        return Response({'sets': services.fetch_sets()})
    except Exception:
        return Response({'detail': 'Unable to reach pokemontcg.io'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
def set_cards(request, set_id):
    try:
        return Response({'cards': services.fetch_set_cards(set_id)})
    except Exception:
        return Response({'detail': 'Unable to reach pokemontcg.io'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
def card_search(request):
    query = request.query_params.get('q', '').strip()
    set_id = request.query_params.get('set', '').strip()
    page = request.query_params.get('page', 1)
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1
    try:
        result = services.search_cards(query, set_id=set_id, page=page)
        return Response(result)
    except Exception:
        return Response({'detail': 'Unable to reach pokemontcg.io'}, status=status.HTTP_502_BAD_GATEWAY)


class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inventory.objects.filter(user=self.request.user).select_related('card')

    def create(self, request, *args, **kwargs):
        api_id = request.data.get('card_api_id')
        quantity = int(request.data.get('quantity', 1))
        card = services.get_or_create_card(api_id, request.data.get('card_data'))
        item, _ = Inventory.objects.get_or_create(user=request.user, card=card)
        item.quantity = quantity
        item.save()
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)


class WantedViewSet(viewsets.ModelViewSet):
    serializer_class = WantedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wanted.objects.filter(user=self.request.user).select_related('card')

    def create(self, request, *args, **kwargs):
        api_id = request.data.get('card_api_id')
        quantity = int(request.data.get('quantity', 1))
        card = services.get_or_create_card(api_id, request.data.get('card_data'))
        item, _ = Wanted.objects.get_or_create(user=request.user, card=card)
        item.quantity = quantity
        item.save()
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def matches(request):
    me = request.user
    my_wanted = set(Wanted.objects.filter(user=me).values_list('card_id', flat=True))
    my_inventory = set(Inventory.objects.filter(user=me).values_list('card_id', flat=True))

    users_ranking = {}
    for other in User.objects.exclude(pk=me.pk).select_related('profile'):
        they_have = set(Inventory.objects.filter(user=other, card_id__in=my_wanted).values_list('card_id', flat=True))
        they_want = set(Wanted.objects.filter(user=other, card_id__in=my_inventory).values_list('card_id', flat=True))
        if they_have or they_want:
            users_ranking[other.id] = {
                'user': UserSerializer(other).data,
                'location': other.profile.location if hasattr(other, 'profile') else '',
                'they_have_count': len(they_have),
                'they_want_count': len(they_want),
                'total': len(they_have) + len(they_want),
            }

    ranked = sorted(users_ranking.values(), key=lambda u: u['total'], reverse=True)
    return Response({'matches': ranked})


@api_view(['GET'])
def match_detail(request, user_id):
    me = request.user
    other = User.objects.get(pk=user_id)
    my_wanted = set(Wanted.objects.filter(user=me).values_list('card_id', flat=True))
    my_inventory = set(Inventory.objects.filter(user=me).values_list('card_id', flat=True))

    cards_they_have = Inventory.objects.filter(user=other, card_id__in=my_wanted).select_related('card')
    cards_they_want = Wanted.objects.filter(user=other, card_id__in=my_inventory).select_related('card')
    cards_i_have_for_them = Inventory.objects.filter(user=me, card_id__in=[
        w.card_id for w in cards_they_want
    ]).select_related('card')

    return Response({
        'user': UserSerializer(other).data,
        'location': other.profile.location if hasattr(other, 'profile') else '',
        'cards_they_have': InventorySerializer(cards_they_have, many=True).data,
        'cards_they_want': WantedSerializer(cards_they_want, many=True).data,
        'cards_i_have_for_them': InventorySerializer(cards_i_have_for_them, many=True).data,
    })


@api_view(['GET'])
def match_rest_inventory(request, user_id):
    """Paginated view of the other user's inventory that doesn't match your want list."""
    me = request.user
    other = User.objects.get(pk=user_id)
    my_wanted = set(Wanted.objects.filter(user=me).values_list('card_id', flat=True))

    qs = Inventory.objects.filter(user=other).exclude(card_id__in=my_wanted).select_related('card')
    total = qs.count()

    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    page_size = 60
    start = (page - 1) * page_size
    items = qs.order_by('card__name')[start:start + page_size]

    return Response({
        'items': InventorySerializer(items, many=True).data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'has_more': start + len(items) < total,
    })


class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Offer.objects.filter(
            Q(offerer=self.request.user) | Q(recipient=self.request.user)
        ).select_related('offerer', 'recipient').prefetch_related('cards__card')

    def create(self, request, *args, **kwargs):
        recipient = User.objects.get(pk=request.data.get('recipient_id'))
        offered = parse_card_quantities(request.data.get('offered', request.data.get('offered_ids', [])))
        requested = parse_card_quantities(request.data.get('requested', request.data.get('requested_ids', [])))

        if not offered and not requested:
            return Response({'detail': 'Offer must include at least one card'}, status=status.HTTP_400_BAD_REQUEST)

        if not _has_cards(request.user, offered):
            return Response({'detail': 'You do not own enough of the offered cards'}, status=status.HTTP_400_BAD_REQUEST)
        if not _has_cards(recipient, requested):
            return Response({'detail': 'The recipient does not have enough of those cards'}, status=status.HTTP_400_BAD_REQUEST)

        offer = Offer.objects.create(offerer=request.user, recipient=recipient, message=request.data.get('message', ''))
        for card_id, quantity in offered:
            OfferCard.objects.create(offer=offer, card_id=card_id, direction='offered', quantity=quantity)
        for card_id, quantity in requested:
            OfferCard.objects.create(offer=offer, card_id=card_id, direction='requested', quantity=quantity)

        return Response(self.get_serializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        offer = self.get_object()
        if offer.recipient != request.user or offer.status != 'pending':
            return Response({'detail': 'Cannot accept this offer'}, status=status.HTTP_400_BAD_REQUEST)
        offer.status = 'accepted'
        offer.offerer_confirmed = False
        offer.recipient_confirmed = False
        offer.save()
        return Response(self.get_serializer(offer).data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        offer = self.get_object()
        if offer.recipient != request.user or offer.status != 'pending':
            return Response({'detail': 'Cannot decline this offer'}, status=status.HTTP_400_BAD_REQUEST)
        offer.status = 'declined'
        offer.save()
        return Response(self.get_serializer(offer).data)

    @action(detail=True, methods=['post'])
    def counter(self, request, pk=None):
        offer = self.get_object()
        if offer.recipient != request.user or offer.status != 'pending':
            return Response({'detail': 'Cannot counter this offer'}, status=status.HTTP_400_BAD_REQUEST)
        old_offerer = offer.offerer
        old_recipient = offer.recipient
        old_message = offer.message
        offer.status = 'countered'
        offer.save()

        new_offer = Offer.objects.create(
            offerer=old_recipient,
            recipient=old_offerer,
            parent=offer,
            message=request.data.get('message', old_message),
        )
        offered = parse_card_quantities(request.data.get('offered', request.data.get('offered_ids', [])))
        requested = parse_card_quantities(request.data.get('requested', request.data.get('requested_ids', [])))
        if not offered and not requested:
            return Response({'detail': 'Offer must include at least one card'}, status=status.HTTP_400_BAD_REQUEST)
        if not _has_cards(old_recipient, offered):
            return Response({'detail': 'You do not own enough of the offered cards'}, status=status.HTTP_400_BAD_REQUEST)
        if not _has_cards(old_offerer, requested):
            return Response({'detail': 'The other user does not have enough of those cards'}, status=status.HTTP_400_BAD_REQUEST)
        for card_id, quantity in offered:
            OfferCard.objects.create(offer=new_offer, card_id=card_id, direction='offered', quantity=quantity)
        for card_id, quantity in requested:
            OfferCard.objects.create(offer=new_offer, card_id=card_id, direction='requested', quantity=quantity)

        return Response(self.get_serializer(new_offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        offer = self.get_object()
        if offer.offerer != request.user or offer.status != 'pending':
            return Response({'detail': 'Cannot cancel this offer'}, status=status.HTTP_400_BAD_REQUEST)
        offer.status = 'cancelled'
        offer.save()
        return Response(self.get_serializer(offer).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        offer = self.get_object()
        if offer.status != 'accepted':
            return Response({'detail': 'Offer must be accepted before confirming'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user == offer.offerer:
            offer.offerer_confirmed = True
        elif request.user == offer.recipient:
            offer.recipient_confirmed = True
        else:
            return Response({'detail': 'Not part of this offer'}, status=status.HTTP_403_FORBIDDEN)
        if offer.offerer_confirmed and offer.recipient_confirmed:
            offer.status = 'confirmed'
            apply_exchange(offer)
        offer.save()
        return Response(self.get_serializer(offer).data)