from django.test import Client, TestCase, override_settings
from django.urls import reverse
import tempfile
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.conf import settings
from django.core.cache import cache

from posts.models import Post, Group, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.follow_user = User.objects.create_user(username='FollowMe')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test_small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Здесь какой то рандомный текст',
                group=cls.group,
                image=uploaded,
            )
        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test_slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': f'{cls.post.author}'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': f'{cls.post.id}'})
            ),
            'posts/create_post.html': (
                reverse('posts:post_edit',
                        kwargs={'pk': f'{cls.post.id}'})
            ),
            'core/404.html': '/unexciting_page/',
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        cls.url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{cls.group.slug}'}),
            reverse('posts:profile', kwargs={'username': f'{cls.post.author}'})
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_uses_correct_template(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_detail_show_correct_context_with_image(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(response.context['post'].text,
                         'Здесь какой то рандомный текст')
        self.assertTrue(
            Post.objects.filter(image='posts/test_small.gif').exists()
        )

    def test_edit_post_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'pk': f'{self.post.id}'}))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_first_page_contains_ten_records(self):
        for url in self.url_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.context['page_obj'].end_index(), 10)
                self.assertIn(self.post, Post.objects.all())
                self.assertTrue(
                    Post.objects.filter(image='posts/test_small.gif').exists()
                )

    def test_second_page_contains_three_records(self):
        for url in self.url_names:
            with self.subTest(url=url):
                response = self.client.get(url + '?page=2')
                self.assertEqual(response.context['page_obj'].end_index(), 13)
                self.assertTrue(
                    Post.objects.filter(image='posts/test_small.gif').exists()
                )

    def test_cash_function(self):
        new_post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Проверка кэша тестовая запись',
        )
        start_content = get_index_content(self)
        new_post.delete()
        content_after_del_post = get_index_content(self)
        self.assertEqual(start_content, content_after_del_post)
        cache.clear()
        content_after_clear_cash = get_index_content(self)
        self.assertNotEqual(content_after_del_post, content_after_clear_cash)

    def test_follow_mechanics(self):
        follow_count = Follow.objects.count()
        self.follow = Follow.objects.create(
            user=self.user,
            author=self.follow_user,
        )
        self.post = Post.objects.create(
            author=self.follow_user,
            text='Супер текст в самый раз для подписки',
        )
        response = self.authorized_client.post(
            reverse('posts:profile_follow', args=[self.follow_user])
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=[self.follow_user])
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.follow_user
        ).exists())

        unfollow_response = self.authorized_client.post(
            reverse('posts:profile_unfollow', args=[self.follow_user], )
        )
        self.assertRedirects(unfollow_response, reverse(
            'posts:profile', args=[self.follow_user]
        ))
        self.assertEqual(Follow.objects.count(), follow_count)


def get_index_content(self):
    return self.authorized_client.get(reverse('posts:index')).content
