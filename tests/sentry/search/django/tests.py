# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime

from sentry.constants import STATUS_RESOLVED, STATUS_UNRESOLVED
from sentry.models import GroupTagValue
from sentry.search.django.backend import DjangoSearchBackend
from sentry.testutils import TestCase


class DjangoSearchBackendTest(TestCase):
    def create_backend(self):
        return DjangoSearchBackend()

    def setUp(self):
        self.backend = self.create_backend()

        self.project1 = self.create_project(name='foo')
        self.project2 = self.create_project(name='bar')

        self.group1 = self.create_group(
            project=self.project1,
            checksum='a' * 40,
            message='foo',
            status=STATUS_UNRESOLVED,
            last_seen=datetime(2013, 8, 13, 3, 8, 24, 880386),
            first_seen=datetime(2013, 7, 13, 3, 8, 24, 880386),
        )
        self.event1 = self.create_event(
            event_id='a' * 40,
            group=self.group1,
            tags={
                'server': 'example.com',
                'env': 'production',
            }
        )

        self.group2 = self.create_group(
            project=self.project1,
            checksum='b' * 40,
            message='bar',
            status=STATUS_RESOLVED,
            last_seen=datetime(2013, 7, 14, 3, 8, 24, 880386),
            first_seen=datetime(2013, 7, 14, 3, 8, 24, 880386),
        )
        self.event2 = self.create_event(
            event_id='b' * 40,
            group=self.group2,
            tags={
                'server': 'example.com',
                'env': 'staging',
                'url': 'http://example.com',
            }
        )

        print self.event1.data['tags'], self.event2.data['tags']

        for key, value in self.event1.data['tags']:
            GroupTagValue.objects.create(
                group=self.group1,
                key=key,
                value=value,
            )
        for key, value in self.event2.data['tags']:
            GroupTagValue.objects.create(
                group=self.group2,
                key=key,
                value=value,
            )

        self.backend.index(self.event1)
        self.backend.index(self.event2)

    def test_query(self):
        backend = self.create_backend()

        results = self.backend.query(self.project1, query='foo')
        assert len(results) == 1
        assert results[0] == self.group1

        results = self.backend.query(self.project1, query='bar')
        assert len(results) == 1
        assert results[0] == self.group2

    def test_sort(self):
        backend = self.create_backend()

        results = self.backend.query(self.project1, sort_by='date')
        assert len(results) == 2
        assert results[0] == self.group1
        assert results[1] == self.group2

        results = self.backend.query(self.project1, sort_by='new')
        assert len(results) == 2
        assert results[0] == self.group2
        assert results[1] == self.group1

    def test_status(self):
        results = self.backend.query(self.project1, status=STATUS_UNRESOLVED)
        assert len(results) == 1
        assert results[0] == self.group1

        results = self.backend.query(self.project1, status=STATUS_RESOLVED)
        assert len(results) == 1
        assert results[0] == self.group2

    def test_tags(self):
        results = self.backend.query(self.project1, tags={'env': 'staging'})
        assert len(results) == 1
        assert results[0] == self.group2

        results = self.backend.query(self.project1, tags={'env': 'example.com'})
        assert len(results) == 0

    def test_project(self):
        results = self.backend.query(self.project2)
        assert len(results) == 0
