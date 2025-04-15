import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from task_planner.configs.config import load_config
from task_planner.main import app

# @pytest.fixture(scope="session", autouse=True)
# def set_test_config():
#     os.environ["CONFIG_FILE"] = "/home/helen/PycharmProjects/tasks_planner/test/test_config.yaml"
#     yield
#     del os.environ["CONFIG_FILE"]


@pytest.fixture(scope="session")
def client():
    config_path = os.getenv("CONFIG_FILE", "test_config.yaml")
    app.state.config = load_config(config_path)

    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.success
def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert all(item in response.text for item in ("Найти задачу",
                                                  "Добавить задачу",
                                                  "Показать все задачи",
                                                  "Обновить задачу",
                                                  "Удалить задачу",
                                                  "Календарь",
                                                  "Скачать задачи"))


# @pytest.mark.failure
# def test_search_task_wrong_start_date(client):
#     response = client.post("/search_task", data={
#         "name": "Test Task 2",
#         "start_year": "2025",
#         "start_month": "02",
#         "start_day": "30",
#         "comment": "This is a test task."
#     })
#     assert response.status_code == 422
#     assert "Вы ввели неправильное начальное время поиска" in response.text


@pytest.mark.failure
def test_search_task_wrong_end_date(client):
    response = client.post("/search_task", data={
        "name": "Test Task 2",
        "end_year": "2025",
        "end_month": "02",
        "end_day": "30",
        "comment": "This is a test task."
    })
    assert response.status_code == 422
    assert "Вы ввели неправильное начальное время поиска" in response.text


@pytest.mark.success
def test_show_all_tasks_no_tasks(client):
    response = client.get("/get_all_tasks")
    assert response.status_code == 404
    assert "/show_task/" not in response.text


@pytest.mark.success
def test_add_task_ok(client):
    response = client.post("/add_task", data={
        "name": "Test Task",
        "year": "2025",
        "month": "10",
        "day": "10",
        "comment": "This is a test task."
    })
    assert response.status_code == 200
    print(response.text)
    assert "Задача добавлена" in response.text


@pytest.mark.success
def test_add_task_existing(client):
    response = client.post("/add_task", data={
        "name": "Test Task",
        "year": "2025",
        "month": "10",
        "day": "10",
        "comment": "This is a test task."
    })
    assert response.status_code == 422
    assert "Задача с таким названием и сроком выполнения уже существует" in response.text


@pytest.mark.failure
def test_add_task_wrong_date(client):
    response = client.post("/add_task", data={
        "name": "Test Task",
        "year": "2025",
        "month": "02",
        "day": "30",
        "comment": "This is a test task."
    })
    assert response.status_code == 422
    assert "Вы ввели неправильное время" in response.text


@pytest.mark.failure
def test_add_task_past_date(client):
    response = client.post("/add_task", data={
        "name": "Test Task",
        "year": "2023",
        "month": "01",
        "day": "22",
        "comment": "This is a test task."
    })
    assert response.status_code == 422
    assert "Введите другое значение для времени выполнения задачи" in response.text


@pytest.mark.success
def test_search_task_by_name_ok(client):
    response = client.post("/search_task", data={
        "name": "Test Task",
    })
    assert response.status_code == 200
    assert "/show_task/" in response.text


@pytest.mark.failure
def test_search_task_by_name_failure(client):
    response = client.post("/search_task", data={
        "name": "Test2",
    })
    assert response.status_code == 404
    assert "Задачи по данным фильтрам не найдены" in response.text


@pytest.mark.success
def test_search_task_by_date_ok(client):
    response = client.post("/search_task", data={
        "year": "2025",
        "month": "10",
        "day": "10",
    })
    assert response.status_code == 200
    assert "/show_task/" in response.text


# @pytest.mark.failure
# def test_search_task_by_date_failure(client):
#     response = client.post("/search_task", data={
#         "end_year": "2025",
#         "end_month": "01",
#         "end_day": "11",
#     })
#     assert response.status_code == 404
#     assert "Задачи по данным фильтрам не найдены" in response.text


@pytest.mark.success
def test_search_task_by_comment_ok(client):
    response = client.post("/search_task", data={
        "comment": "This is a test task."
    })
    assert response.status_code == 200
    assert "/show_task/" in response.text

#
# @pytest.mark.failure
# def test_search_task_by_comment_failure(client):
#     response = client.post("/search_task", data={
#         "comment": "1111111"
#     })
#     assert response.status_code == 404
#     assert "Задачи по данным фильтрам не найдены" in response.text


@pytest.mark.success
def test_search_task_by_status_ok(client):
    response = client.post("/search_task", data={
        "done": "False"
    })
    assert response.status_code == 200
    assert "/show_task/" in response.text

#
# @pytest.mark.failure
# def test_search_task_by_status_failure(client):
#     response = client.post("/search_task", data={
#         "done": "True"
#     })
#     assert response.status_code == 404
#     assert "Задачи по данным фильтрам не найдены" in response.text


@pytest.mark.success
def test_update_task_ok(client):
    response = client.post("/update_task", data={
        "name": "Test Task",
        "year": "2025",
        "month": "10",
        "day": "10",
        "new_year": "2025",
        "new_month": "11",
        "new_day": "11",
        "comment": "New test comment."
    })
    assert response.status_code == 200
    assert "Задача обновлена" in response.text


@pytest.mark.failure
def test_update_task_not_found(client):
    response = client.post("/update_task", data={
        "name": "Test2",
        "year": "2025",
        "month": "10",
        "day": "10",
        "comment": "New new test comment."
    })
    assert response.status_code == 404
    assert "не найдена" in response.text

#
# @pytest.mark.failure
# def test_update_task_past_date(client):
#     response = client.post("/update_task", data={
#         "name": "Test Task",
#         "year": "2025",
#         "month": "11",
#         "day": "11",
#         "new_year": "2022",
#         "new_month": "11",
#         "new_day": "11",
#     })
#     assert response.status_code == 422
#     assert "Введите другое значение для времени выполнения задачи" in response.text


@pytest.mark.failure
def test_update_task_wrong_date(client):
    response = client.post("/update_task", data={
        "name": "Test Task",
        "year": "2025",
        "month": "02",
        "day": "30",
        "comment": "New test comment."
    })
    assert response.status_code == 422
    assert "Вы ввели неправильное время" in response.text


@pytest.mark.success
def test_show_all_tasks_ok(client):
    response = client.get("/get_all_tasks")
    assert response.status_code == 200
    assert "/show_task/" in response.text


@pytest.mark.success
def test_delete_task_ok(client):
    response = client.post("/delete_task", data={
        "name": "Test Task",
        "year": "2025",
        "month": "11",
        "day": "11",
    })
    assert response.status_code == 200
    assert "Задача удалена" in response.text


@pytest.mark.failure
def test_delete_task_not_found(client):
    response = client.post("/delete_task", data={
        "name": "Test Task",
        "year": "2025",
        "month": "11",
        "day": "11",
    })
    assert response.status_code == 404
    assert "не найдена" in response.text


@pytest.mark.failure
def test_delete_task_bad_request(client):
    response = client.post("/delete_task", data={
        "name": "Test Task",
    })
    assert response.status_code == 422
    assert "Чтобы удалить задачу введите её название и срок выполнения." in response.text

