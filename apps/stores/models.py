from django.db import models


class StoreStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DRAFT = "draft", "Draft"
    ARCHIVED = "archived", "Archived"


class Store(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=64, blank=True, default="")
    cluster_tag = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(
        max_length=16, choices=StoreStatus.choices, default=StoreStatus.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Department(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    cad_seeded = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = [("store", "name")]

    def __str__(self) -> str:
        return f"{self.store.name} / {self.name}"


class Aisle(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="aisles")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aisles",
    )
    name = models.CharField(max_length=120)
    number = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["number", "name"]

    def __str__(self) -> str:
        return f"{self.store.name} / {self.name}"
