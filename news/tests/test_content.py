"""
+ Количество новостей на главной странице — не более 10.
+ Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
+ Комментарии на странице отдельной новости отсортированы
    от старых к новым: старые в начале списка, новые — в конце.
+ Анонимному пользователю не видна форма для отправки комментария
    на странице отдельной новости, а авторизованному видна.
"""
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News

User = get_user_model()


class TestHomePage(TestCase):
    """Тест контента домашней страницы."""
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных для тестов."""
        today = datetime.today()
        News.objects.bulk_create(
            News(
                title=f'Новость {index}',
                text='Просто текст.',
                date=today - timedelta(days=index)
            )
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        )

    def test_news_count(self):
        """Проверка работы настройки количества выводимых новостей."""
        print('Тест домашней страницы')
        # Загружаем главную страницу.
        response = self.client.get(self.HOME_URL)
        # Код ответа не проверяем, его уже проверили в тестах маршрутов.
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        # Определяем длину списка.
        news_count = len(object_list)
        print(f'\tКоличество новостей на странице: {news_count}')

        # Проверяем, что на странице именно 10 новостей.
        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        """Проверка сортировки новостей: от новых к старым."""
        print('Тест сортировки новостей')
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        # Получаем даты новостей в том порядке, как они выведены на странице.
        all_dates = [news.date for news in object_list]
        # Сортируем полученный список по убыванию.
        sorted_dates = sorted(all_dates, reverse=True)

        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_dates, sorted_dates)


class TestDetailPage(TestCase):
    """Тест подробной страницы новости."""

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Тестовая новость', text='Просто текст.'
        )
        # Сохраняем в переменную адрес страницы с новостью:
        cls.detail_url = reverse('news:detail', args=(cls.news.id,))
        cls.author = User.objects.create(username='Комментатор')
        # Запоминаем текущее время:
        now = timezone.now()
        # print(now)
        # Создаём комментарии в цикле.
        for index in range(2):
            # Создаём объект и записываем его в переменную.
            comment = Comment.objects.create(
                news=cls.news, author=cls.author, text=f'Tекст {index}',
            )
            # Сразу после создания меняем время создания комментария.
            comment.created = now + timedelta(days=index)
            print(
                f'Комментарий №{index + 1} - '
                f'{comment.created:%Y.%m.%d (%H:%M)}'
            )
            # И сохраняем эти изменения.
            comment.save()

    def test_comments_order(self):
        """Тест сортировки комментариев."""
        print("""Тест сортировки комментариев.""")
        response = self.client.get(self.detail_url)

        # Проверяем, что объект новости находится в словаре контекста
        # под ожидаемым именем - названием модели.
        self.assertIn('news', response.context)
        # Получаем объект новости.
        news = response.context['news']
        # Получаем все комментарии к новости.
        all_comments = news.comment_set.all()
        # Проверяем, что время создания первого комментария в списке
        # меньше, чем время создания второго.
        self.assertLess(all_comments[0].created, all_comments[1].created)

    def test_anonymous_client_has_no_form(self):
        """Видит ли аноним форму?"""
        print("""Видит ли аноним форму?""")
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)

    def test_authorized_client_has_form(self):
        """Видит ли авторизованный юзер форму?"""
        print("""Видит ли авторизованный юзер форму?""")
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)
