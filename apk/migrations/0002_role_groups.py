from django.db import migrations

ROLE_GROUP_NAMES = ["MVD", "Chilonzor"]


def create_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for group_name in ROLE_GROUP_NAMES:
        if not Group.objects.filter(name__iexact=group_name).exists():
            Group.objects.create(name=group_name)


def remove_role_groups(apps, schema_editor):
    """Guruhlarni faqat hech kim a'zo bo'lmagan holda o'chiradi."""
    Group = apps.get_model("auth", "Group")
    for group_name in ROLE_GROUP_NAMES:
        group = Group.objects.filter(name__iexact=group_name).first()
        if group and not group.user_set.exists():
            group.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("apk", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_role_groups, remove_role_groups),
    ]
