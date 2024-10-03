import json
import os

from nocodb.nocodb import Nocodb, Base, Table

from nocodb import prepare_json

# nocodb_host = 'http://192.168.11.104:8080'
nocodb_host = 'https://data.casus.science'
nocodb_token = os.getenv('NOCODB_TOKEN')
ndb = Nocodb(nocodb_host, nocodb_token)
title = 'base title'

description = 'base description'
base_color = '#C0708'
table_color = '#e6f253'
base_id: str


def create_base() -> dict:
    base_type = Base.Type.database
    dict = ndb.create_base(title, base_color, description, base_type)
    global base_id
    base_id = dict['id']
    return dict


def delete_base():
    res = ndb.delete_base(base_id)
    # print(res)


def test_list_base():
    bases = ndb.list_bases()
    assert len(bases) == 0
    create_base()
    bases = ndb.list_bases()
    assert len(bases) == 1
    # FIXME
    # assert title in bases[0]
    delete_base()


def test_create_base():
    res = create_base()
    assert res['title'] == title
    assert res['color'] == base_color
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
    assert base['color'] == base_color
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
        table_id = base.create_table('table test name', columns, color=table_color)
        table = Table(table_id, host=nocodb_host, auth_token=nocodb_token)
        table_meta = table.read_table()
        # print(table_dict)

        ints, floats, durations, datetimes, urls, texts, bools, lists = 0, 0, 0, 0, 0, 0, 0, 0
        for c in table_meta['columns']:
            print(c)
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
        # assert floats == 143
        # assert durations == 2
        # assert datetimes == 1
        assert urls == 1
        assert texts == 78
        assert bools == 63
        assert lists == 8

        delete_base()

# Broken because of bugs
# def int_bigint_promotion():
def test_int_bigint_promotion():
    table = Table('m15rrl1rn2vzskk', host=nocodb_host, auth_token=nocodb_token)
    r = table.read_table_record('https://codebase.helmholtz.cloud/casus-datalad/flame_data/project/-/tree/master/newest_pc2/case_flame_pc2_balanced.p1.5G')
    base_dict = create_base()
    with open('DATASET.json', 'r') as f:
        json_input = json.load(f)
        pk = 0
        data = prepare_json.prepare_input(json_input, extra={'Primary Key': pk, 'status': "current"})
        special_columns = [{
            "column_name": "Primary Key",
            "title": "Primary Key",
            "uidt": "ID",
            "dt": "int",
            "un": False,
            "pk": True  # primary key
        }, {
            "column_name": "status",
            "title": "status",
            "uidt": "SingleSelect",
            "dt": "character varying",
            "dtx": "specificType",
            "dtxp": "'current','deleted','replaced'",
            "dtxs": "",
            "cdf": "'current'"
        }]
        columns = special_columns + prepare_json.derive_table_columns_definition(data)
        base = ndb.get_base_object(base_dict['title'])
        table_id = base.create_table('table test name', columns, color=table_color)
        table = Table(table_id, host=nocodb_host, auth_token=nocodb_token)
        res = table.insert(data)
        assert res['Primary Key'] == pk

        res = table.update_record(pk, 'SLURM.SLURM_CPUS_ON_NODE', 2)
        # assert 'Wert »62702371781194950« ist außerhalb des gültigen Bereichs für Typ integer' in res['msg']

        # res = table.update_record(pk, 'SLURM.SLURM_CPUS_ON_NODE', 2)

        delete_base()
