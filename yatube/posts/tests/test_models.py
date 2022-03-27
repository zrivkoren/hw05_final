from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names_post(self):
        post = PostModelTest.post
        name_post = post.text
        post_label = post._meta.get_field('text').help_text
        group_verbose_name = post._meta.get_field('group').verbose_name
        self.assertEqual(name_post, str(post))
        self.assertEqual(post_label, 'Введите текст поста')
        self.assertEqual(group_verbose_name, 'Группа')

    def test_models_have_correct_object_names_group(self):
        group = PostModelTest.group
        name_group = group.title
        self.assertEqual(name_group, str(group))
