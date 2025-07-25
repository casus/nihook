# import json
# import os
#
# import requests
#
# from gitlab_webhooks import nocodb
#
# tableid = 'm15rrl1rn2vzskk'
# nocodb_host = 'https://data.casus.science'
# nocodb_token = ''
# table = nocodb.Table(tableid, host=nocodb_host, auth_token=nocodb_token, verify=False)
#
# # get the old entry
# old = table.list()
# print(json.dumps(old, indent=4))
#
# # assert 'list' in old
# # assert 1 == len(old['list'])
# #
# # # modify the entry
# # old_record = old['list'][0]
# #
# # old_url = old_record['URL']
# # print("PRE: ", old_record['URL'], old_record['status'])
# #
# # old_record['URL'] = projecturl + "/-/commit/" + commit_before
# # old_record['status'] = 'deleted'
# #
# # # remove Nocodb's system fields
# # old_record.pop('CreatedAt')
# # old_record.pop('UpdatedAt')
# #
# # print("POST: ", old_record['URL'], old_record['status'])
# #
# # # insert the old entry with modified URL and status -- because we cannot update the primary key
# # print("INSERT")
# # res = table.insert(old_record)
# #
# # print("DELETE")
# # # delete the originalö entry
# # res = table.delete()
#
# # data = requests.get('https://data.casus.science:8080/api/v2/tables/m15rrl1rn2vzskk/records/1',
# #                     headers={"accept": "application/json", "xc-token": nocodb_token},
# #                     verify=False)
# # print(data)
#
# res = requests.delete('https://data.casus.science/api/v2/tables/m15rrl1rn2vzskk/records',
#                       headers={"accept": "application/json", "xc-token": nocodb_token},
#                       data= { "URL": "https://codebase.helmholtz.cloud/casus-datalad/flame_data/project/-/tree/master/newest_pc2/case_flame_pc2_balanced.p1.9" },
#                       verify=False)
# print(json.dumps(res.json(), indent=4))
