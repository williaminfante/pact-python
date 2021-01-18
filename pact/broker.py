"""API for creating a contract and configuring the mock service."""
from __future__ import unicode_literals

import fnmatch
import os
from subprocess import Popen

from .constants import BROKER_CLIENT_PATH

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Broker():
    """PactBroker helper functions."""

    def __init__(self, broker_base_url=None, broker_username=None, broker_password=None, broker_token=None):
        self.broker_base_url = broker_base_url
        self.broker_username = broker_username
        self.broker_password = broker_password
        self.broker_token = broker_token

    def _get_broker_base_url(self):
        return self.broker_base_url or os.environ["PACT_BROKER_BASE_URL"]

    @staticmethod
    def _normalize_consumer_name(name):
        return name.lower().replace(' ', '_')

    def publish(self, consumer_name, version, pact_dir=None,
                tag_with_git_branch=None, consumer_tags=None):
        """Publish the generated pact files to the specified pact broker."""
        if self.broker_base_url is None \
                and "PACT_BROKER_BASE_URL" not in os.environ:
            raise RuntimeError("No pact broker URL specified. "
                               + "Did you expect the PACT_BROKER_BASE_URL "
                               + "environment variable to be set?")

        pact_files = fnmatch.filter(
            os.listdir(pact_dir),
            self._normalize_consumer_name(consumer_name) + '*.json'
        )
        command = [
            BROKER_CLIENT_PATH,
            'publish',
            '--consumer-app-version={}'.format(version)]

        command.append('--broker-base-url={}'.format(self._get_broker_base_url()))

        if self.broker_username is not None:
            command.append('--broker-username={}'.format(self.broker_username))
        if self.broker_password is not None:
            command.append('--broker-password={}'.format(self.broker_password))
        if self.broker_token is not None:
            command.append('--broker-token={}'.format(self.broker_token))

        command.extend(pact_files)

        if tag_with_git_branch:
            command.append('--tag-with-git-branch')

        if consumer_tags is not None:
            for tag in consumer_tags:
                command.extend(['-t', tag])

        print(f"PactBroker command: {command}")

        publish_process = Popen(command)
        publish_process.wait()
        if publish_process.returncode != 0:
            url = self._get_broker_base_url()
            raise RuntimeError(
                "There was an error while publishing to the "
                + "pact broker at {}."
                .format(url))