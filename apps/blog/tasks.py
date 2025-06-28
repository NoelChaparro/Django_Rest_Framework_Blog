import logging
from celery import shared_task
import redis
from .models import PostAnalytics, Post
from django.conf import settings

logger = logging.getLogger(__name__)
redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=6379,db=0)

@shared_task
def increment_post_impressions(post_id):
    logger.info(f"Update post impressions for post_id: {post_id}")
    """
    Increment the impressions count for a post.
    """
    try:
        analytics, created = PostAnalytics.objects.get_or_create(post__id=post_id)
        analytics.increment_impression()
    except Exception as e:
        logger.error(f"Error incrementing impressions for post_id {post_id}: {str(e)}")
        
@shared_task
def sync_impressions_to_db():
    """
    Sincronizar las impresiones almacenadas en redis con la base de datos.
    """
    keys = redis_client.keys('post:impressions:*')
    for key in keys:
        post_id = key.decode('utf-8').split(':')[-1]
        impressions = int(redis_client.get(key) or 0)
        
        if impressions:
            try:
                analytics, created = PostAnalytics.objects.get_or_create(post__id=post_id)
                analytics.impressions += impressions
                analytics.save()
                analytics._update_click_through_rate()
                
                # Clear the redis key after syncing
                redis_client.delete(key)
            except Exception as e:
                logger.error(f"Error syncing impressions for post_id {post_id}: {str(e)}")

@shared_task
def increment_post_views_task(slug, ip_address):
    """
    Incrementa las vistas de un post
    """
    try:
        post = Post.objects.get(slug=slug)
        post_analytics, created = PostAnalytics.objects.get_or_create(post__slug=slug)
        post_analytics.increment_view(ip_address)
    except Exception as e:
        logger.error(f"Error incrementing views for post slug {slug}: {str(e)}")
