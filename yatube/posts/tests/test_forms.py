from django.test import Client, TestCase, override_settings
from django.urls import reverse
import tempfile
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Post, User, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Здесь какой то рандомный текст',
            group=cls.group,
        )
        cls.form_date_edit_post = {
            'text': 'Тестируем  нового поста форму создания',
        }
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.form_date_create_post = {
            'text': 'Тестируем создания нового поста форму',
            'image': cls.uploaded,
        }
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Вот он такой тестовый комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_with_image(self):
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_date_create_post,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': f'{self.post.author}'}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(
            Post.objects.get(id=2).text, self.form_date_create_post['text']
        )
        self.assertTrue(Post.objects.filter(
            image=f'posts/{self.uploaded.name}'
        ).exists())

    def test_edit_post(self):
        post_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(f'{self.post.id}',)),
            data=self.form_date_edit_post,
            follow=True
        )

        self.assertEqual(
            response.context['post'].text, self.form_date_edit_post['text']
        )
        self.assertEqual(post_count, Post.objects.count())
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(f'{self.post.id}',))
        )

    def test_create_comment_on_detail_page(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(response.context['comments'][0], self.comment)

        guest_response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertRedirects(
            guest_response,
            reverse('users:login') + f"?next=/posts/{self.post.id}/comment/"
        )
