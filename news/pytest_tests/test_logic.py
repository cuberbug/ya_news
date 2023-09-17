"""
+ Анонимный пользователь не может отправить комментарий.
+ Авторизованный пользователь может отправить комментарий.
+ Если комментарий содержит запрещённые слова,
    он не будет опубликован, а форма вернёт ошибку.
+ Авторизованный пользователь может редактировать
    или удалять свои комментарии.
+ Авторизованный пользователь не может редактировать
    или удалять чужие комментарии.
"""
from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import WARNING
from news.models import Comment


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id_for_args')),
    )
)
def test_anonymous_user_cant_create_comment(client, name, args, form_data):
    """Проверка невозможности создания заметки анонимным пользователем."""
    url = reverse(name, args=args)
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.exists() is False


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id_for_args')),
    )
)
def test_user_can_create_comment(
    author, author_client, name, args, form_data, news
):
    """Проверка возможности создания заметки авторизованным пользователем."""
    url = reverse(name, args=args)
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    assert Comment.objects.exists() is True
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id_for_args')),
    )
)
def test_user_cant_use_bad_words(
    bad_words_data, author_client, name, args
):
    """Проверка блокировки стоп-слов."""
    url = reverse(name, args=args)
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    assert Comment.objects.exists() is False


def test_author_can_delete_comment(
    author_client, news_id_for_args, comment_id_for_args
):
    """Проверка возможности удаления комментария автором."""
    url = reverse('news:detail', args=news_id_for_args)
    delete_url = reverse('news:delete', args=comment_id_for_args)
    response = author_client.delete(delete_url)
    assertRedirects(response, f'{url}#comments')
    assert Comment.objects.exists() is False


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(
    user_client, comment_id_for_args
):
    """Проверка невозможности удаления чужого комментария."""
    url = reverse('news:delete', args=comment_id_for_args)
    response = user_client.delete(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.exists() is True
    assert Comment.objects.count() == 1


def test_author_can_edit_comment(
    author_client, comment_id_for_args, form_data, news_id_for_args, comment
):
    """Проверка возможности редактирования комментария автором."""
    url = reverse('news:edit', args=comment_id_for_args)
    response = author_client.post(url, data=form_data)
    url_to_comments = reverse('news:detail', args=news_id_for_args)
    assertRedirects(response, f'{url_to_comments}#comments')
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_user_cant_edit_comment_of_another_user(
    user_client, comment_id_for_args, form_data, comment
):
    """Проверка невозможности редактирования чужого комментария."""
    url = reverse('news:edit', args=comment_id_for_args)
    response = user_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text
