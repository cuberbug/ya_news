"""
Анонимный пользователь не может:
    + отправить комментарий.
Авторизованный пользователь может
    + отправить комментарий.
Если комментарий содержит запрещённые слова, он
    + не будет опубликован.
Авторизованный пользователь может
    + редактировать или удалять свои комментарии.
Авторизованный пользователь не может
    + редактировать или удалять чужие комментарии.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


class TestCommentCreation(TestCase):
    # Текст комментария понадобится в нескольких местах кода,
    # поэтому запишем его в атрибуты класса.
    COMMENT_TEXT = 'Текст комментария'

    @classmethod
    def setUpTestData(cls):
        print('\n>>> Tест создания комментария:\n')
        print('Подготовка данных для тестов:')
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        # Адрес страницы с новостью.
        cls.url = reverse('news:detail', args=(cls.news.id,))
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании комментария.
        cls.form_data = {'text': cls.COMMENT_TEXT}

        print(f'\t>создан пользователь: {cls.user}')
        print(
            '\t>создана тестовая заметка:'
            f' {cls.news.title} - {cls.news.text}'
        )

    def test_anonymous_user_cant_create_comment(self):
        """Проверка невозможности создания заметки анонимным пользователем."""
        print('\nТест отправки POST-запроса на создание коммента от анонима:')
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество комментариев.
        comments_count = Comment.objects.count()
        # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
        self.assertEqual(comments_count, 0)

        if comments_count == 0:
            print('\t>> OK')

    def test_user_can_create_comment(self):
        """
        Проверка возможности создания заметки авторизованным пользователем.
        """
        print('\nТест отправки POST-запроса на создание коммента от юзера:')
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с комментами.
        self.assertRedirects(response, f'{self.url}#comments')
        # Считаем количество комментариев.
        comments_count = Comment.objects.count()
        # Убеждаемся, что есть один комментарий.
        self.assertEqual(comments_count, 1)
        # Получаем объект комментария из базы.
        comment = Comment.objects.get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)

        if (
            comments_count == 1
            and comment.text == self.COMMENT_TEXT
            and comment.news == self.news
            and comment.author == self.user
        ):
            print('\t>> OK')

    def test_user_cant_use_bad_words(self):
        """Проверка блокировки стоп-слов."""
        print('\nПроверка блокировки стоп-слов:')
        # Формируем данные для отправки формы; текст включает
        # первое слово из списка стоп-слов.
        bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
        # Отправляем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=bad_words_data)
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            form='form',
            field='text',
            errors=WARNING
        )
        # Дополнительно убедимся, что комментарий не был создан.
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)

        if comments_count == 0:
            print('\t>> OK')


class TestCommentEditDelete(TestCase):
    # Тексты для комментариев не нужно дополнительно создавать
    # (в отличие от объектов в БД), им не нужны ссылки на self или cls,
    # поэтому их можно перечислить просто в атрибутах класса.
    COMMENT_TEXT = 'Текст комментария'
    NEW_COMMENT_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        print('\n>>> Tест редактирования и удаления комментария:\n')
        print('Подготовка данных для тестов:')
        # Создаём новость в БД.
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        # Формируем адрес блока с комментариями,
        # который понадобится для тестов.
        news_url = reverse('news:detail', args=(cls.news.id,))  # новости
        cls.url_to_comments = news_url + '#comments'  # блока с комментариями
        # Создаём пользователя - автора комментария.
        cls.author = User.objects.create(username='Автор комментария')
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём объект комментария.
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT
        )
        # URL для редактирования комментария.
        cls.edit_url = reverse('news:edit', args=(cls.comment.id,))
        # URL для удаления комментария.
        cls.delete_url = reverse('news:delete', args=(cls.comment.id,))
        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

        print(f'\t>созданы пользователи: {cls.author}, {cls.reader}')
        print(f'\t>создана тестовая заметка: {cls.comment.text}')
        print('=============================================')

    def test_author_can_delete_comment(self):
        """Проверка возможности удаления комментария автором."""
        print('\nТест удаления комментария автором:')
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)

        # Проверяем, что редирект привёл к разделу с комментариями.
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.url_to_comments)
        # Считаем количество комментариев в системе.
        comments_count = Comment.objects.count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(comments_count, 0)

        if comments_count == 0:
            print('\t>> OK')

    def test_user_cant_delete_comment_of_another_user(self):
        """Проверка невозможности удаления чужого комментария."""
        print('\nТест удаления комментария читателем:')
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)

        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)

        if comments_count == 1 and response.status_code == 404:
            print('\t>> OK')

    def test_author_can_edit_comment(self):
        """Проверка возможности редактирования комментария автором."""
        print('\nТест редактирования комментария автором:')
        # Выполняем запрос на редактирование от имени автора комментария.
        response = self.author_client.post(self.edit_url, data=self.form_data)

        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.url_to_comments)
        # Обновляем объект комментария.
        self.comment.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

        if self.comment.text == self.NEW_COMMENT_TEXT:
            print('\t>> OK')

    def test_user_cant_edit_comment_of_another_user(self):
        """Проверка невозможности редактирования чужого комментария."""
        print('\nТест редактирования комментария читателем:')
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)

        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.comment.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.comment.text, self.COMMENT_TEXT)

        if (
            self.comment.text == self.COMMENT_TEXT
            and response.status_code == 404
        ):
            print('\t>> OK')
