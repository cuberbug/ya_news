from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
import pytest

from news.models import Comment, News


@pytest.fixture
def author(django_user_model):
    """Модель пользователя-автора."""
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    """Залогиненный в клиенте автор."""
    client.force_login(author)
    return client


@pytest.fixture
def news() -> News:
    """Модель новости."""
    news = News.objects.create(
        title='Заголовок',
        text='Текст новости',
    )
    return news


@pytest.fixture
def news_for_count() -> News:
    """Модель списка новостей для подсчёта."""
    today = datetime.today()
    news_for_count = News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )
    return news_for_count


@pytest.fixture
def new_id_for_args(news: News) -> tuple:
    """ID для новости."""
    return news.id,


@pytest.fixture
def comment(author, news: News) -> Comment:
    """Модель комментария к новости."""
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария',
    )
    return comment


@pytest.fixture
def comment_for_count(author, news: News) -> Comment:
    """Модель комментариев для подсчёта."""
    now = timezone.now()
    for index in range(2):
        comment_for_count = Comment.objects.create(
            news=news,
            author=author,
            text=f'Tекст {index}',
        )
        comment_for_count.created = now + timedelta(days=index)
        comment_for_count.save()
    return comment_for_count


@pytest.fixture
def comment_id_for_args(comment: Comment) -> tuple:
    """ID для коммента."""
    return comment.id,
