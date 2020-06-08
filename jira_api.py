import requests
import json
from requests.auth import HTTPBasicAuth
from django.conf import settings

class JiraRequests():

    def _get(self, url, headers, data=[]):
        return requests.request("GET", url, auth=HTTPBasicAuth(settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN), headers=headers, data=data)

    def _post(self,url, headers, data):
        return requests.request("POST",url,auth=HTTPBasicAuth(settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN),data=data,headers=headers)

    def create_organization(self,name):
        url = "https://{}.atlassian.net/rest/servicedeskapi/organization".format(settings.JIRA_DOMAIN)
        headers = {"Accept": "application/json","Content-Type": "application/json"}
        payload = json.dumps({"name": name})
        response = self._post(url, headers, payload)
        return json.loads(response.text)

    def get_organizations(self):
        url = "https://{}.atlassian.net/rest/servicedeskapi/organization".format(settings.JIRA_DOMAIN)
        headers = {"Accept": "application/json"}
        response = self._get(url,headers)
        return response.text

    def get_organization(self, organizationId):
        url = "https://{}.atlassian.net/rest/servicedeskapi/organization/{}".format(settings.JIRA_DOMAIN, organizationId)
        headers = {"Accept": "application/json"}
        response = self._get(url,headers)
        return json.loads(response.text)

    def get_users_in_organization(self,organizationId):
        url = "https://{}.atlassian.net/rest/servicedeskapi/organization/{}/user".format(settings.JIRA_DOMAIN, organizationId)
        headers = {"Accept": "application/json"}
        response = self._get(url,headers)
        return json.loads(response.text)

    def create_customer(self,user):
        url = "https://{}.atlassian.net/rest/servicedeskapi/customer".format(settings.JIRA_DOMAIN)
        headers = {"Accept": "application/json","Content-Type": "application/json"}
        payload = json.dumps({"displayName": user['displayName'],"email": user['email']})
        response = self._post(url,headers,payload)
        return json.loads(response.text)

    def add_customer_to_organization(self,organizationId, accountId):
        url = "https://{}.atlassian.net/rest/servicedeskapi/organization/{}/user".format(settings.JIRA_DOMAIN, organizationId)
        headers = {"Content-Type": "application/json"}
        payload = json.dumps({"accountIds": [accountId,],})
        response = self._post(url,headers,payload)
        return json.loads(response.text)

    def get_requst_type(self,serviceDeskKey):
        url = "https://{}.atlassian.net/rest/servicedeskapi/servicedesk/{}/requesttype".format(settings.JIRA_DOMAIN, serviceDeskKey)
        headers = {"Accept": "application/json"}
        response = self._get(url, headers)
        return json.loads(response.text)

    def _get_id_organization(self, user):
        organizations = self.get_organizations()
        for organization in organizations['values']:
            if organization['name'] == settings.COMPANY_DOMAIN:
                for user_jira in self.get_users_in_organization(organization['id'])['values']:
                    if user_jira['emailAddress'] == user['email']:
                        break
                else:
                    new_customer = self.create_customer(user)
                    self.add_customer_to_organization(organization['id'], new_customer['accountId'])
                return organization['id']
        new_organization = self.create_organization(settings.COMPANY_DOMAIN)
        new_customer = self.create_customer(user)
        self.add_customer_to_organization(new_organization['id'], new_customer['accountId'])
        return new_organization['id']

    def filter_all_task_by_organization(self, organizationId):
        url = "https://{}.atlassian.net/rest/servicedeskapi/request".format(settings.JIRA_DOMAIN, )
        headers = {"Accept": "application/json"}
        data = {'organizationId': organizationId,'requestOwnership': 'ORGANIZATION'}
        response = self._get(url, headers)
        return json.loads(response.text)

    def get_all_task(self, user):
        jira_organizations = self.get_organizations()
        organizationId = None
        url = "https://{}.atlassian.net/rest/servicedeskapi/request".format(settings.JIRA_DOMAIN, )
        if jira_organizations['values']:
            for organization in jira_organizations['values']:
                if organization['name'] == settings.COMPANY_DOMAIN:
                    organizationId = organization['id']
                    break
        else:
            new_organization = self.create_organization(settings.COMPANY_DOMAIN)
            new_customer = self.create_customer(user)
            self.add_customer_to_organization(new_organization['id'], new_customer['accountId'])
            organizationId = new_organization['id']
        headers = {"Accept": "application/json"}
        data = {'organizationId': organizationId, 'requestOwnership': 'ORGANIZATION'}
        response = self._get(url, headers,data=data)
        return json.loads(response.text)

    def create_task(self,serviceDeskId,requestTypeId='',summary='', description='',user={}):
        organization_id = self.__get_id_organization(user)
        url = "https://{}.atlassian.net/rest/servicedeskapi/request".format(settings.JIRA_DOMAIN)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = json.dumps({
                "serviceDeskId": serviceDeskId,
                "requestTypeId": requestTypeId,
                "raiseOnBehalfOf": user['email'],
                "requestFieldValues":{
                    "summary": summary,
                    "description": description,
                    'customfield_10002': [int(organization_id),]
                }
        })
        response = self._post(url,headers,payload)
        return json.loads(response.text)

    def add_comment(self, issueIdOrKey, text, public=True):
        url = "https://{}.atlassian.net/rest/api/2/issue/{}/comment".format(settings.JIRA_DOMAIN, issueIdOrKey)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = json.dumps({"public": public, "body": text})
        response = self._post(url, headers, payload)
        return json.loads(response.text)

    def add_file_to_task(self,issueIdOrKey,file_name,text,public=True):
        url = "https://{}.atlassian.net/rest/api/2/issue/{}/attachments".format(settings.JIRA_DOMAIN, issueIdOrKey)
        headers = {"X-Atlassian-Token": "nocheck"}
        files = {'file': open(file_name,'rb')}
        payload = {"public": public, "additionalComment": {"body": text}}
        response = requests.post(url, auth=HTTPBasicAuth(settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN), files=files, data=payload, headers=headers)
        return json.loads(response.text)

    def get_name_task(self,issueIdOrKey):
        url = "https://{}.atlassian.net/rest/api/2/issue/{}".format(settings.JIRA_DOMAIN, issueIdOrKey)
        headers = {"Accept": "application/json"}
        response = self._get(url, headers)
        return json.loads(response.text)

    def get_description_task(self, issueIdOrKey):
        url = "https://{}.atlassian.net/rest/api/2/issue/{}".format(settings.JIRA_DOMAIN, issueIdOrKey)
        headers = {"Accept": "application/json"}
        response = self._get(url, headers)
        return json.loads(response.text)


    def get_customer_request_status(self, issueIdOrKey):
        url = "https://{}.atlassian.net/rest/servicedeskapi/request/{}/status".format(settings.JIRA_DOMAIN, issueIdOrKey)
        headers = {"Accept": "application/json"}
        response = self._get(url, headers)
        return json.loads(response.text)

    def get_sla_by_id(self,issueIdOrKey,id_sla):
        url = "https://{}.atlassian.net/rest/servicedeskapi/request/{}/sla/{}".format(settings.JIRA_DOMAIN, issueIdOrKey, id_sla)
        headers = {"Accept": "application/json"}
        response = self._get(url, headers)
        return json.loads(response.text)

    def get_SLA(self,issueIdOrKey):
        url = "https://{}.atlassian.net/rest/servicedeskapi/request/{}/sla".format(settings.JIRA_DOMAIN, issueIdOrKey)
        headers = {"Accept": "application/json"}
        response = self._get(url, headers)
        return json.loads(response.text)

    def get_categories(self,issueIdOrKey):
        url = "https://{}.atlassian.net/rest/api/2/issue/{}".format(settings.JIRA_DOMAIN, issueIdOrKey)
        headers = {"Accept": "application/json"}
        response = self._get(url, headers)
        return json.loads(response.text)