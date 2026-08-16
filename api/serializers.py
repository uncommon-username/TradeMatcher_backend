from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Card, Inventory, Offer, OfferCard, UserProfile, Wanted


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        UserProfile.objects.create(user=user)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('user_id', 'username', 'email', 'location')


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ('id', 'api_id', 'name', 'set_id', 'set_name', 'number', 'rarity', 'image_small', 'image_large')


class InventorySerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)
    card_api_id = serializers.CharField(write_only=True)

    class Meta:
        model = Inventory
        fields = ('id', 'card', 'card_api_id', 'quantity')


class WantedSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)
    card_api_id = serializers.CharField(write_only=True)

    class Meta:
        model = Wanted
        fields = ('id', 'card', 'card_api_id', 'quantity')


class OfferCardSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = OfferCard
        fields = ('id', 'card', 'direction', 'quantity')


class OfferSerializer(serializers.ModelSerializer):
    offerer = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    cards = OfferCardSerializer(many=True, read_only=True)
    offered_ids = serializers.ListField(write_only=True, child=serializers.IntegerField())
    requested_ids = serializers.ListField(write_only=True, child=serializers.IntegerField())

    class Meta:
        model = Offer
        fields = (
            'id', 'offerer', 'recipient', 'parent_id', 'status', 'message',
            'offerer_confirmed', 'recipient_confirmed',
            'created_at', 'updated_at', 'cards', 'offered_ids', 'requested_ids',
        )