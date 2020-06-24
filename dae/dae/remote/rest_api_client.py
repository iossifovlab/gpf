import requests


class RESTClient:

    def __init__(
            self, remote_id, host,
            username, password,
            base_url=None, port=None):
        self.host = host
        self.remote_id = remote_id
        self.username = username
        self.password = password
        if base_url:
            if not base_url.endswith("/"):
                base_url = base_url + "/"
            if not base_url.startswith("/"):
                base_url = "/" + base_url
            self.base_url = base_url
        else:
            self.base_url = "/"

        if port:
            self.port = port
        else:
            self.port = 8000

        self.session = self._login()

    def _login(self):
        login_url = "users/login"
        session = requests.session()
        data = {
            "username": self.username,
            "password": self.password
        }
        login_url = self._build_url(login_url)
        response = session.post(login_url, data=data)
        assert response.status_code == 204
        return session

    def _build_url(self, url, query_values=None):
        query_url = url
        if query_values:
            first = False
            for k, v in query_values.items():
                query_url += "?" if first else "&"
                query_url += f"{k}={v}"
        result = f"http://{self.host}:{self.port}{self.base_url}{query_url}"
        return result

    def _get(self, url, query_values=None, stream=False):
        url = self._build_url(url, query_values)
        response = self.session.get(url, stream=stream)
        return response

    def _post(self, url, data=None, stream=False):
        url = self._build_url(url)
        response = self.session.post(url, json=data, stream=stream)
        return response

    def _put(self, url, data=None):
        pass

    def _delete(self, url, data=None):
        pass

    def get_remote_dataset_id(self, dataset_id):
        return f"{self.remote_id}_{dataset_id}"

    def get_datasets(self):
        response = self._get("datasets")
        if response.status_code == 200:
            return response.json()

    def get_dataset_config(self, study_id):
        response = self._get(f"datasets/{study_id}")
        if response.status_code == 200:
            return response.json()["data"]

    def get_variants_preview(self, data):
        response = self._post(
            "genotype_browser/preview/variants",
            data=data,
            stream=True
        )
        return response

    def get_browser_preview_info(self, data):
        response = self._post("genotype_browser/preview", data=data)
        return response

    def get_common_report(self, common_report_id):
        response = self._get(f"common_reports/studies/{common_report_id}")
        return response.json()

    def get_common_report_families_data(self, common_report_id):
        response = self._get(
            f"common_reports/families_data/{common_report_id}",
            stream=True
        )
        return response
