from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException
from .models import Post, Heading, PostView, PostAnalytics
from .serializers import PostSerializer, PostListSerializer, HeadingSerializer
from .utils import get_client_ip
from .tasks import increment_post_impressions
import redis
from django.conf import settings
from core.permissions import HasValidAPIKey
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .tasks import increment_post_views_task
from rest_framework_api.views import StandardAPIView
from rest_framework import status

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=6379,db=0)

# class PostlistView(ListAPIView):
#     queryset = Post.postobjects.all()
#     serializer_class = PostListSerializer

class PostlistView(StandardAPIView):
    permission_classes = [HasValidAPIKey]
    

    def get(self, request, *args, **kwargs):
        try:
            #Verificar si los datos estan en cache
            cached_posts = cache.get('post_list')
            if cached_posts:
                # Serializar los datos del cache
                serialized_posts = PostListSerializer(cached_posts, many= True).data
                #Incrementar impresiones en Redis
                for post in serialized_posts:
                    redis_client.incr(f'post:impressions:{post.id}')
                return self.paginate(request, serialized_posts)
            #obtener los posts desde la base de datos si no estan en cache
            posts = Post.postobjects.all()
            
            if not posts.exists():
                raise NotFound(detail="No posts found", code=404)
            
            serializer = PostListSerializer(posts, many=True)
            #guardar los datos en cache
            cache.set('post_list', posts, timeout=60 * 5)  # Cache for 5 minute
            
            for post in posts:
                redis_client.incr(f'post:impressions:{post.id}')

                
        except Post.DoesNotExist:
            raise NotFound(detail="Posts not found", code=404)
        except Exception as e:
            raise APIException(detail=f'An unexcpected error ocurred: {str(e)}', code=500)
        
        return self.paginate_response_with_extra(request, serializer.data, extra_data="Extra data can be added here")

# class PostDetailView(RetrieveAPIView):
#     queryset = Post.postobjects.all()
#     serializer_class = PostSerializer
#     lookup_field = 'slug'

class PostDetailView(StandardAPIView):
    permission_classes = [HasValidAPIKey]
    
    #@method_decorator(cache_page(60 * 1))
    def get(self, request, slug):
        ip_address = get_client_ip(request)
        try:
            # Verificar si los datos estan en cache
            cached_post = cache.get(f'post_detail_{slug}')
            if cached_post:
                cached_slug = cached_post.get('slug')
                if cached_slug:
                    increment_post_views_task.delay(cached_slug, ip_address)
                else:
                    increment_post_views_task.delay(slug, ip_address)
                return self.response(cached_post, status=status.HTTP_200_OK)
            
            #si no esta en cache, obtener el post de la base de datos
            
            post = Post.postobjects.get(slug=slug)
            serializer = PostSerializer(post)
            #guardar los datos en cache
            cache.set(f'post_detail_{slug}', serializer.data, timeout=60 * 5)  # Cache for 5 minute
            #Incrementar vistas en segundo plano
            increment_post_views_task.delay(post.slug, ip_address)
        except Post.DoesNotExist:
            raise NotFound(detail="Post not found", code=404)
        except Exception as e:
            raise APIException(detail=f'An unexcpected error ocurred: {str(e)}', code=500)     
        
        return self.response(serializer.data, status=status.HTTP_200_OK)


class PostHeadingsView(ListAPIView):
    permission_classes = [HasValidAPIKey]
    serializer_class = HeadingSerializer

    def get_queryset(self):
        post_slug = self.kwargs.get('slug')
        return Heading.objects.filter(post__slug=post_slug)

class IncrementPostClickView(APIView):
    permission_classes = [HasValidAPIKey]
    
    def post(self, request):
        """
        Increment the click count for a post identified by its slug.
        """
        data = request.data
        try:
            post = Post.postobjects.get(slug=data['slug'])
        except Post.DoesNotExist:
            raise NotFound(detail="Post not found", code=404)
        except PostAnalytics.DoesNotExist:
            raise NotFound(detail="Post analytics not found", code=404)
        except Exception as e:
            raise APIException(detail=f'An error ocurred while incrementing click: {str(e)}', code=500)
        
        try:
            post_analytics, created = PostAnalytics.objects.get_or_create(post=post)
            post_analytics.increment_click()
        except Exception as e:
            raise APIException(detail=f'An error ocurred while updating post analytics: {str(e)}', code=500)
        
        return Response({
            "message": "Click incremented successfully",
            "clicks": post_analytics.clicks
        })