import requests


class RESTClient:

    def __init__(self, host, base_url=None, port=None):
        self.host = host
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
        username = "admin@iossifovlab.com"
        password = "secret"
        login_url = "users/login"
        session = requests.session()
        data = {
            "username": username,
            "password": password
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

    def _get(self, url, query_values=None):
        url = self._build_url(url, query_values)
        response = self.session.get(url)
        return response

    def _post(self, url, data=None):
        url = self._build_url(url)
        response = self.session.post(url, json=data)
        return response

    def _put(self, url, data=None):
        pass

    def _delete(self, url, data=None):
        pass

    def get_datasets(self):
        response = self._get("datasets")
        print(response.headers)
        if response.status_code == 200:
            return response.json()

    def get_dataset_config(self, study_id):
        response = self._get(f"datasets/{study_id}")
        if response.status_code == 200:
            return response.json()["data"]

    def get_variants_preview(self, data):
        response = self._post("genotype_browser/preview/variants", data=data)
        return response
