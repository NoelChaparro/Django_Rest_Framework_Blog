from django.test import TestCase
from django.urls import reverse
from .models import Category, Post, PostAnalytics
from rest_framework.test import APIClient
from django.conf import settings


# Views Tests
class PostListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="API", slug="api")
        self.api_key = settings.VALID_API_KEYS[0]
        self.post = Post.objects.create(
            title="API Testing",
            description="Testing API endpoints",
            content="This is a test post for API testing.",
            slug="api-testing",
            category=self.category,
            status="published"
        )
    
    def test_get_post_list(self):
        url=reverse('post-list')
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )
        
        print(response.json())
        
        data = response.json()
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('status', data)
        self.assertEqual(data['status'], 200)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        
        result = data['results']
        self.assertEqual(len(result), 1)
        
        post_data = result[0]
        self.assertEqual(post_data['id'], str(self.post.id))
        self.assertEqual(post_data['title'], self.post.title)
        self.assertEqual(post_data['description'], self.post.description)
        self.assertEqual(post_data['thumbnail'])
        self.assertEqual(post_data['slug'], self.post.slug)
        
        category_data = post_data['category']
        self.assertEqual(category_data['name'], self.category.name)
        self.assertEqual(category_data['slug'], self.category.slug)
        
        self.assertEqual(post_data['view_count'], 0)        
        self.assertIsNone(data['next'])
        self.assertIsNone(data['previous'])




# Models Test
class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Tech',
            title="Technology",
            description='This is a test category for unit testing.',
            slug='tech',
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Tech')
        self.assertEqual(self.category.title, 'Technology')
        self.assertEqual(self.category.description, 'This is a test category for unit testing.')
        self.assertEqual(self.category.slug, 'tech')

class PostModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Tech',
            title="Technology",
            description='This is a test category for unit testing.',
            slug='tech',
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post for unit testing.',
            category=self.category,
            slug='test-post',
            status='published'
        )

    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.content, 'This is a test post for unit testing.')
        self.assertEqual(self.post.category, self.category)
        self.assertEqual(self.post.slug, 'test-post')
    
    def test_post_published_manager(self):
        self.assertTrue(Post.postobjects.filter(status='published').exists())

class PostAnalyticsModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Tech',
            title="Technology",
            description='This is a test category for unit testing.',
            slug='tech',
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post for unit testing.',
            category=self.category,
            slug='test-post',
            status='published'
        )
        self.analytics = PostAnalytics.objects.create(post=self.post)

    def test_post_analytics_creation(self):
        self.analytics.increment_impression()
        self.analytics.increment_click()
        self.analytics.refresh_from_db()
        self.assertEqual(self.analytics.click_through_rate, 100.0)