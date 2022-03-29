from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Post, Group, User


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Здесь какой то рандомный текст',
        )
        cls.templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test_slug/',
            'posts/profile.html': f'/profile/{cls.post.author}/',
            'posts/post_detail.html': f'/posts/{cls.post.pk}/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_random_url_404(self):
        response = self.guest_client.get('/unexciting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


    def test_urls_correct_template(self):
        for template, url in self.templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_create_post(self):
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_edit_post(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
