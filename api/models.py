from django.contrib.auth.models import User
from django.db import models


class Card(models.Model):
    api_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    set_id = models.CharField(max_length=64)
    set_name = models.CharField(max_length=255)
    number = models.CharField(max_length=16)
    rarity = models.CharField(max_length=64, blank=True)
    image_small = models.URLField(blank=True)
    image_large = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.set_id}-{self.number})"


class PokemonSet(models.Model):
    api_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    series = models.CharField(max_length=255, blank=True)
    release_date = models.CharField(max_length=32, blank=True)
    total = models.IntegerField(null=True, blank=True)
    logo_url = models.URLField(blank=True)
    symbol_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    location = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.user.username


class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'card'], name='unique_inventory_card'),
        ]

    def __str__(self):
        return f"{self.user.username} owns {self.quantity}x {self.card.name}"


class Wanted(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wanted')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='wanted_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'card'], name='unique_wanted_card'),
        ]

    def __str__(self):
        return f"{self.user.username} wants {self.quantity}x {self.card.name}"


class Offer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('confirmed', 'Confirmed'),
        ('declined', 'Declined'),
        ('countered', 'Countered'),
        ('cancelled', 'Cancelled'),
    ]

    offerer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers_made')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers_received')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    offerer_confirmed = models.BooleanField(default=False)
    recipient_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Offer {self.offerer} -> {self.recipient} ({self.status})"


class OfferCard(models.Model):
    DIRECTION_CHOICES = [
        ('offered', 'Offered'),
        ('requested', 'Requested'),
    ]

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='cards')
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    direction = models.CharField(max_length=16, choices=DIRECTION_CHOICES)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.direction}: {self.quantity}x {self.card.name}"