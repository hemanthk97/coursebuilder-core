# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Integration tests for the GraphQL service."""

__author__ = [
    'John Orr (jorr@google.com)',
]

import json

from tests.integration import integration
from tests.integration import pageobjects
from tests import suite


class QueryApp(pageobjects.PageObject):
    URI = '/modules/gql/_static/query/index.html'

    def load(self):
        self.get(suite.TestBase.INTEGRATION_SERVER_BASE_URL + self.URI)
        return self

    def assert_query_text(self, text):
        elt = self.find_element_by_css_selector('textarea[ng-model="query"]')
        self._tester.assertEquals(text, elt.get_attribute('value'))
        return self

    def set_query_text(self, query_text):
        elt = self.find_element_by_css_selector('textarea[ng-model="query"]')
        elt.clear()
        elt.send_keys(query_text)
        return self

    def click_query_button(self):
        self.find_element_by_css_selector('button.query-button').click()
        return self

    def assert_result_text(self, expected_result_text):
        expected_result_dict = json.loads(expected_result_text)
        actual_result_dict = json.loads(
            self.find_element_by_css_selector('md-card-content.result').text)
        self._tester.assertEquals(expected_result_dict, actual_result_dict)
        return self

    def assert_result_criteria(self, result_criteria_function):
        # Pass the results dict to the criteria function and assert it succeeds
        result_dict = json.loads(
            self.find_element_by_css_selector('md-card-content.result').text)
        self._tester.assertTrue(result_criteria_function(result_dict))

    def assert_error_list(self, expected_error_list):
        li_list = self.find_elements_by_css_selector(
            'md-card-content.errors li')
        actual_error_list = [li.text for li in li_list]
        self._tester.assertEquals(expected_error_list, actual_error_list)
        return self

    def assert_logged_out(self):
        self._tester.assertEquals(
            'Login',
            self.find_element_by_css_selector('cb-login .login-link').text)
        return self

    def assert_logged_in(self, login_name):
        self._tester.assertEquals(
            'Logout',
            self.find_element_by_css_selector('cb-login .logout-link').text)
        self._tester.assertEquals(
            login_name,
            self.find_element_by_css_selector('cb-login .login-name').text)
        return self

    def click_login(self):
        self.find_element_by_link_text('Login').click()
        return pageobjects.LoginPage(self._tester, continue_page=QueryApp)

    def click_logout(self):
        self.find_element_by_link_text('Logout').click()
        return self


class QueryAppTests(integration.TestBase):

    def setUp(self):
        super(QueryAppTests, self).setUp()
        self.set_gql_service_enabled(True)

    def tearDown(self):
        self.set_gql_service_enabled(False)
        super(QueryAppTests, self).tearDown()

    def set_gql_service_enabled(self, enabled):
        self.load_root_page(
        ).click_login(
        ).login(
            self.LOGIN, admin=True
        ).click_dashboard(
        ).click_site_settings(
        ).click_override(
            'gcb_gql_service_enabled'
        ).set_status(
            'Active'
        ).set_value(
            enabled
        ).click_save()

        self.load_root_page().click_logout()

    def test_login_logout(self):
        QueryApp(self).load(
        ).assert_logged_out(
        ).click_login(
        ).login(
            self.LOGIN, admin=True
        ).assert_logged_in(
            self.LOGIN
        ).click_logout(
        ).assert_logged_out()

    def test_default_query(self):
        default_query = (
            '{\n'
            '  allCourses {\n'
            '    edges {\n'
            '      node {id title}\n'
            '    }\n'
            '  }\n'
            '}\n')
        expected_result = (
            '{'
            '  "allCourses": {'
            '    "edges": ['
            '      {'
            '        "node": {'
            '          "title": "Power Searching with Google",'
            '          "id": "UNKNOWN"'
            '        }'
            '      }'
            '    ]'
            '  }'
            '}')
        def result_criteria(actual_result_dict):
            expected_result_dict = json.loads(expected_result)
            # Accept the actual course id as received
            expected_result_dict['allCourses']['edges'][0]['node']['id'] = (
                actual_result_dict['allCourses']['edges'][0]['node']['id'])
            return actual_result_dict == expected_result_dict

        QueryApp(self).load(
        ).assert_query_text(
            default_query
        ).click_query_button(
        ).assert_result_criteria(
            result_criteria
        )

    def test_error_messages(self):
        query_with_error = '{ unknownField }'

        QueryApp(self).load(
        ).set_query_text(
            query_with_error
        ).click_query_button(
        ).assert_error_list(
          ['Cannot query field "unknownField" on "Query".']
        )
