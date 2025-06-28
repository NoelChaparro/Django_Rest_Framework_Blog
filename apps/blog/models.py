import uuid
from django.utils import timezone
from django.utils.html import format_html
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from .utils import get_client_ip
from core.storage_backends import PublicMediaStorage

from apps.media.models import Media
from apps.media.serializers import MediaSerializer


def blog_thumbnail_directory(instance, filename):
    sanitized_title = instance.title.replace(" ","_")
    return 'thumbnails/blog/{0}/{1}'.format(sanitized_title, filename)

def category_thumbnail_directory(instance, filename):
    sanitized_name = filename.title.replace(" ","_")
    return 'thumbnails/blog_categories/{0}/{1}'.format(sanitized_name, filename)

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    #thumbnail = models.ImageField(upload_to=category_thumbnail_directory, blank=True, null=True)
    thumbnail = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        related_name='category',
        blank=True,
        null=True
    )
    slug = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    
    def thumbnail_preview(self):
        if self.thumbnail:
            serializer = MediaSerializer(instance=self.thumbnail)
            url = serializer.data.get('url')
            if url:
                return format_html('<image src="{}" style="width: 100px; height: auto;" />', url)
        
        return 'No thumbnail'
    
    thumbnail_preview.short_description = "Thumbnail Preview"

class Post(models.Model):

    class PostObjects(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(status='published')
    
    status_options = (
        ('draft', 'Draft'),
        ('published', 'Published')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=256)
    content = CKEditor5Field('Content', config_name='default')
    #thumbnail = models.ImageField(upload_to=blog_thumbnail_directory, storage=PublicMediaStorage)
    thumbnail = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        related_name='post',
        blank=True,
        null=True
    )
    keywords = models.CharField(max_length=128)
    slug = models.CharField(max_length=128)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='posts')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=status_options, default='draft')
    objects = models.Manager()  # Default manager
    postobjects = PostObjects()  # Custom manager for published posts


    class Meta:
        ordering = ['status', '-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
    
    def __str__(self):
        return self.title
    
    def thumbnail_preview(self):
        if self.thumbnail:
            serializer = MediaSerializer(instance=self.thumbnail)
            url = serializer.data.get('url')
            if url:
                return format_html('<image src="{}" style="width: 100px; height: auto;" />', url)
        
        return 'No thumbnail'
    
    thumbnail_preview.short_description = "Thumbnail Preview"

class PostView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_view')
    ip_addres = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

class PostAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_analytics')
    views = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    click_through_rate = models.FloatField(default=0)
    average_time_on_page = models.FloatField(default=0)

    def increment_click(self):
        self.clicks += 1
        self.save()
        self._update_click_through_rate()
    
    def _update_click_through_rate(self):
        if self.impressions > 0:
            self.click_through_rate = (self.clicks / self.impressions) * 100
        else:
            self.click_through_rate = 0
        self.save()

    def increment_impression(self):
        self.impressions += 1
        self.save()
        self._update_click_through_rate()
    
    def increment_view(self, ip_address):
        if not PostView.objects.filter(post=self.post, ip_addres=ip_address).exists():
            PostView.objects.create(post=self.post, ip_addres=ip_address)
            self.views += 1
            self.save()

class Heading(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='headings')
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    level = models.IntegerField(
        choices=(
            (1, 'H1'),
            (2, 'H2'),
            (3, 'H3'),
            (4, 'H4'),
            (5, 'H5'),
            (6, 'H6'),
        )
    )
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Heading'
        verbose_name_plural = 'Headings'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

@receiver(post_save, sender=Post)
def create_post_analytics(sender, instance, created, **kwargs):
    if created:
        PostAnalytics.objects.create(post=instance)
        