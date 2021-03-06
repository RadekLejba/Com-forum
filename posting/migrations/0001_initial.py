# Generated by Django 3.0 on 2020-03-02 22:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('created', models.DateField(auto_now_add=True)),
                ('description', models.CharField(blank=True, max_length=500)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('closed', models.DateField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('last_post_added', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posting.Board')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(default='')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated', models.BooleanField(default=False)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('hidden', models.BooleanField(blank=True, null=True)),
                ('starting_post', models.BooleanField(default=False)),
                ('file', models.ImageField(blank=True, upload_to='')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='posting.Post')),
                ('refers_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referrers_set', to='posting.Post')),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posting.Thread')),
            ],
        ),
    ]
