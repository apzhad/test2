import pytest
from fixture.generic import Generic
from fixture.db import DbFixture
from fixture.orm import ORMFixture
import json
import os.path
import importlib
import jsonpickle

fixture = None
settings = None


def load_config(file):
    global settings
    if settings is None:
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
        with open(config_file) as f:
            settings = json.load(f)
    return settings


@pytest.fixture
def gen(request):
    global fixture
    browser = request.config.getoption("--browser")
    web_conf = load_config(request.config.getoption("--settings"))["web"]
    if fixture is None or not fixture.is_valid():
        fixture = Generic(browser=browser, base_url=web_conf["base_url"])
    fixture.session.ensure_login(username=web_conf["username"], password=web_conf["password"])
    return fixture


@pytest.fixture(scope="session")
def db(request):
    db_conf = load_config(request.config.getoption("--settings"))["db"]
    dbfixture = DbFixture(host=db_conf["host"], name=db_conf["name"], user=db_conf["username"],
                          password=db_conf["password"])

    def fin():
        dbfixture.finish()
    request.addfinalizer(fin)
    return dbfixture


@pytest.fixture(scope="session")
def orm(request):
    orm_conf = load_config(request.config.getoption("--settings"))["db"]
    ormfixture = ORMFixture(host=orm_conf["host"], name=orm_conf["name"], user=orm_conf["username"],
                            password=orm_conf["password"])
    return ormfixture


@pytest.fixture(scope="session", autouse=True)
def stop(request):
    def fin():
        fixture.session.ensure_logout()
        fixture.finish()
    request.addfinalizer(fin)
    return fixture


@pytest.fixture
def check_ui(request):
    return request.config.getoption("--check_ui")


def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="firefox")
    parser.addoption("--settings", action="store", default="settings.json")
    parser.addoption("--check_ui", action="store_true")


def pytest_generate_tests(metafunc):
    """
    This allows us to load tests from external files by
    parametrizing tests with each test case found in a data_X
    file
    https://remusao.github.io/posts/pytest-param.html
    """
    for fixture in metafunc.fixturenames:
        if fixture.startswith('data_'):
            # Load associated test data
            testdata = load_from_module(fixture[5:])
            metafunc.parametrize(fixture, testdata, ids=[str(x) for x in testdata])
        elif fixture.startswith('json_'):
            testdata = load_from_json(fixture[5:])
            metafunc.parametrize(fixture, testdata, ids=[str(x) for x in testdata])


def load_from_module(module):
    return importlib.import_module("data.%s" % module).test_data


def load_from_json(file):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/%s.json" % file)) as f:
        return jsonpickle.decode(f.read())
