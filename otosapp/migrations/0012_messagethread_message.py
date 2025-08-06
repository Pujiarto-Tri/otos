# Generated for messaging system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('otosapp', '0011_user_profile_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageThread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Judul thread pesan', max_length=200)),
                ('thread_type', models.CharField(choices=[('academic', 'Pertanyaan Materi'), ('technical', 'Masalah Teknis/Aplikasi'), ('report', 'Pelaporan Masalah'), ('general', 'Umum')], default='general', max_length=20)),
                ('status', models.CharField(choices=[('open', 'Terbuka'), ('pending', 'Menunggu Respons'), ('resolved', 'Selesai'), ('closed', 'Ditutup')], default='open', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('priority', models.CharField(choices=[('low', 'Rendah'), ('normal', 'Normal'), ('high', 'Tinggi'), ('urgent', 'Mendesak')], default='normal', max_length=10)),
                ('category', models.ForeignKey(blank=True, help_text='Kategori materi (untuk pertanyaan akademik)', null=True, on_delete=django.db.models.deletion.SET_NULL, to='otosapp.category')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_threads', to=settings.AUTH_USER_MODEL)),
                ('teacher_or_admin', models.ForeignKey(blank=True, help_text='Guru atau admin yang menangani', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='handled_threads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Thread Pesan',
                'verbose_name_plural': 'Thread Pesan',
                'ordering': ['-last_activity'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='Isi pesan')),
                ('attachment', models.FileField(blank=True, help_text='File lampiran (opsional)', null=True, upload_to='message_attachments/')),
                ('is_read', models.BooleanField(default=False)),
                ('is_edited', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='otosapp.messagethread')),
            ],
            options={
                'verbose_name': 'Pesan',
                'verbose_name_plural': 'Pesan',
                'ordering': ['created_at'],
            },
        ),
    ]
