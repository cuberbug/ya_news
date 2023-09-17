"""
План тестирования:

+ Количество новостей на главной странице — не более 10.
+ Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
+ Комментарии на странице отдельной новости отсортированы от старых к новым:
    старые в начале списка, новые — в конце.
+ Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости, а авторизованному доступна.
"""
import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    'parametrized_client',
    (
        (pytest.lazy_fixture('client')),
        (pytest.lazy_fixture('admin_client')),
    ),
    ids=['Client', 'Admin_client']
)
def test_news_list_for_different_users(
        news, parametrized_client
):
    """Проверка отображения контекста для всех пользователей."""
    url = reverse('news:home')
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    assert news in object_list


@pytest.mark.django_db
@pytest.mark.parametrize(
    'parametrized_client, form_in_detail',
    (
        (pytest.lazy_fixture('client'), False),
        (pytest.lazy_fixture('admin_client'), True),
    ),
    ids=['Other_User', 'Author']
)
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id_for_args')),
    ),
    ids=['Detail']
)
def test_pages_contains_form(
    parametrized_client, name, args, form_in_detail
):
    """Проверка наличия формы в переменной контекста."""
    url = reverse(name, args=args)
    response = parametrized_client.get(url)
    assert ('form' in response.context) is form_in_detail


@pytest.mark.django_db
def test_news_count(news_for_count, client):
    """Проверка работы настройки количества выводимых новостей."""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(news_for_count, client):
    """Проверка сортировки новостей: от новых к старым."""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id_for_args')),
    ),
    ids=['Detail']
)
def test_comments_order(
    comment_for_count, client, name, args
):
    """Проверка сортировки комментариев: от старых к новым."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    assert all_comments[0].created < all_comments[1].created
