"""
Django signals for automatic business creation on user registration.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import User
from apps.businesses.models import Business, BusinessSchedule
import datetime

@receiver(post_save, sender=User)
def create_user_business(sender, instance, created, **kwargs):
    """
    Automatically create a business entity when a new user registers.
    Also generate a default schedule (Mon-Fri 09:00 to 18:00).
    """
    if created:
        business = Business.objects.create(
            owner=instance,
            name=f"{instance.first_name}'s Business",
        )
        
        # Create default schedules
        schedules = []
        for i in range(7):
            if i < 5:  # Monday to Friday
                schedules.append(BusinessSchedule(
                    business=business, day_of_week=i, 
                    start_time=datetime.time(9, 0), end_time=datetime.time(18, 0)
                ))
            else:  # Saturday and Sunday closed
                schedules.append(BusinessSchedule(
                    business=business, day_of_week=i,
                    is_closed=True
                ))
        BusinessSchedule.objects.bulk_create(schedules)
