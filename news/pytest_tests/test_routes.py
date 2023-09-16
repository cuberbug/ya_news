"""
План тестирования:

+ Главная страница доступна анонимному пользователю.
+ Страница отдельной новости доступна анонимному пользователю.
+ Страницы удаления и редактирования комментария доступны автору комментария.
+ При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
+ Авторизованный пользователь не может зайти на страницы редактирования
    или удаления чужих комментариев (возвращается ошибка 404).
+ Страницы регистрации пользователей, входа в учётную запись и выхода из неё
    доступны анонимным пользователям.
"""
from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:home', None),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
        ('news:detail', pytest.lazy_fixture('new_id_for_args')),
    ),
    ids=['Homepage', 'Login', 'Logout', 'Signup', 'Detail']
)
def test_home_availability_for_anonymous_user(client, name, args):
    """
    Тест доступности страниц для анонима:
    * главная;
    * логин;
    * логаут;
    * регистрация;
    * подробная страница новости.
    """
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    print(f'Аноним - запрос к url:{url} >>> {response.status_code}')


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
    ids=['Other_user', 'Author']
)
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', pytest.lazy_fixture('comment_id_for_args')),
        ('news:delete', pytest.lazy_fixture('comment_id_for_args')),
    ),
    ids=['Edit', 'Delete']
)
def test_pages_availability_for_auth_user(
    parametrized_client, expected_status, name, args,
):
    """
    Тест доступности страниц для автора и юзера:
    * редактирование комментария;
    * удаление комментария.
    """
    url = reverse(name, args=args)
    response = parametrized_client.get(url)
    assert response.status_code == expected_status

    print(f'url:...{url} >>> {response.status_code}')


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', pytest.lazy_fixture('comment_id_for_args')),
        ('news:delete', pytest.lazy_fixture('comment_id_for_args')),
    ),
    ids=['Edit', 'Delete']
)
def test_redirects(client, name, args):
    """Тест редиректа анонима с недоступных ему страниц."""
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)

    print(f'url:...{url} >>> {response.status_code} >>> {expected_url}')
