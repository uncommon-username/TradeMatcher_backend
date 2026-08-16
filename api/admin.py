from django.contrib import admin

from .models import Card, Inventory, Offer, OfferCard, PokemonSet, UserProfile, Wanted


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'set_name', 'number', 'rarity')
    search_fields = ('name', 'api_id')


@admin.register(PokemonSet)
class PokemonSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'series', 'release_date', 'total')
    search_fields = ('name', 'api_id')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location')


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'quantity')


@admin.register(Wanted)
class WantedAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'quantity')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('offerer', 'recipient', 'status', 'created_at')


@admin.register(OfferCard)
class OfferCardAdmin(admin.ModelAdmin):
    list_display = ('offer', 'card', 'direction', 'quantity')