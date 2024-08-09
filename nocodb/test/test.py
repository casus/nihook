import json
import os

from nocodb.nocodb import Nocodb, Base, Table

from nocodb import prepare_json

nocodb_host = 'http://192.168.11.104:8080'
nocodb_token = os.getenv('NOCODB_TOKEN')
ndb = Nocodb(nocodb_host, nocodb_token)
title = 'base title'

description = 'base description'
color = '#C0708'
base_id: str


def create_base() -> dict:
    base_type = Base.Type.database
    dict = ndb.create_base(title, color, description, base_type)
    global base_id
    base_id = dict['id']
    return dict


def delete_base():
    res = ndb.delete_base(base_id)
    print(res)


def test_list_base():
    bases = ndb.list_bases()
    assert len(bases) == 0
    create_base()
    bases = ndb.list_bases()
    assert len(bases) == 1
    assert title in bases
    delete_base()


def test_create_base():
    res = create_base()
    assert res['title'] == title
    assert res['color'] == color
    assert res['description'] == description
    # there is no `type` in return
    # assert res['type'] == base_type
    res = ndb.delete_base(res['id'])
    assert res == True


def test_get_base_object():
    create_base()
    base = ndb.get_base_object(title)
    assert base is not None
    delete_base()


def test_get_base_info():
    create_base()
    base = ndb.get_base_object(title)
    info = base.get_base_info()
    assert info['Arch'] == 'x64'
    assert info['Docker'] == False
    assert info['Node'] == 'v20.11.1'
    assert info['PackageVersion'] == '0.204.9'
    assert info['Platform'] == 'linux'
    assert info['RootDB'] == 'sqlite3'
    delete_base()


def test_get_base():
    create_base()
    base = ndb.get_base_object(title)
    base = base.get_base()
    assert base['title'] == title
    assert base['description'] == description
    assert base['color'] == color
    delete_base()


# def test_list_tables():
#     base_dict = create_base()
#     base = ndb.get_base_object(base_dict['title'])
#     base.create_table()
#     tables = base.list_tables()
#     assert 'Table' in tables
#     delete_base()

# This checks if `DATASET.json` definition fields can be properly derived.
# Note: this works fine also for
def test_derivative_table_columns_definition():
    base_dict = create_base()
    with open('DATASET.json', 'r') as f:
        json_input = json.load(f)
        data = prepare_json.prepare_input(json_input)
        columns = prepare_json.derive_table_columns_definition(data)

        ints, floats, durations, datetimes, urls, texts, bools, lists = 0, 0, 0, 0, 0, 0, 0, 0
        for c in columns:
            # print(c)
            match c['uidt']:
                case 'Number':
                    if c['dt'] == 'int':
                        ints += 1
                    elif c['dt'] == 'float8':
                        floats += 1
                    else:
                        raise Exception(f'invalid dt type {c["dt"]}')
                case 'Duration':
                    durations += 1
                case 'DateTime':
                    datetimes += 1
                case 'URL':
                    urls += 1
                case 'SingleLineText':
                    texts += 1
                case 'Checkbox':
                    bools += 1
                case 'JSON':
                    lists += 1

        assert ints == 121
        assert floats == 142
        assert durations == 2
        assert datetimes == 1
        assert urls == 1
        assert texts == 78
        assert bools == 63
        assert lists == 8

        delete_base()


def test_read_table_columns():
    base_dict = create_base()
    with open('DATASET.json', 'r') as f:
        json_input = json.load(f)
        data = prepare_json.prepare_input(json_input)
        columns = prepare_json.derive_table_columns_definition(data)
        base = ndb.get_base_object(base_dict['title'])
        table_id = base.create_table('table test name', columns, color="#e6f253")
        table = Table(table_id, host=nocodb_host, auth_token=nocodb_token)
        table_dict = table.read_table()
        # print(table_dict)

        ints, floats, durations, datetimes, urls, texts, bools, lists = 0, 0, 0, 0, 0, 0, 0, 0
        for c in table_dict['columns']:
            match c['uidt']:
                case 'Number':
                    if c['dt'] == 'int':
                        ints += 1
                    elif c['dt'] == 'float8':
                        floats += 1
                    else:
                        raise Exception(f'invalid dt type {c["dt"]}')
                case 'Duration':
                    durations += 1
                case 'DateTime':
                    datetimes += 1
                case 'URL':
                    urls += 1
                case 'SingleLineText':
                    texts += 1
                case 'Checkbox':
                    bools += 1
                case 'JSON':
                    lists += 1

        assert ints == 121
        assert floats == 142
        assert durations == 2
        assert datetimes == 1
        assert urls == 1
        assert texts == 78
        assert bools == 63
        assert lists == 8

        # delete_base()
