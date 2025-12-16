from ckanapi import RemoteCKAN
from ckanapi.errors import CKANAPIError

class CKAN():
    def init_app(self, app):
        self.app = app
        self.ua = (
            'waarismijnstemlokaal/1.0 (+https://waarismijnstemlokaal.nl/)'
        )
        self.ckanapi = RemoteCKAN(
            app.config['CKAN_URL'],
            apikey=app.config['CKAN_API_KEY'],
            user_agent=self.ua
        ).action
        self.elections = app.config['CKAN_CURRENT_ELECTIONS']

    def create_datastore(self, resource_id, fields):
        self.ckanapi.datastore_create(
            resource_id=resource_id,
            force=True,
            fields=fields,
            primary_key=['UUID']
        )

    def resource_show(self, resource_id):
        return self.ckanapi.resource_show(
            id=resource_id
        )

    def delete_datastore(self, resource_id):
        self.ckanapi.datastore_delete(
            resource_id=resource_id,
            force=True
        )

    def _get_resources_metadata(self):
        resources_metadata = {}
        for election_key, election_value in self.elections.items():
            resources_metadata[election_key] = {}
            try:
                resources_metadata[election_key]['publish_resource'] = (
                    self.ckanapi.resource_show(
                        id=election_value['publish_resource']
                    )
                )
            except CKANAPIError as e:
                self.app.logger.error(
                    'Can\'t get publish resource metadata: %s' % (e)
                )

            try:
                resources_metadata[election_key]['draft_resource'] = (
                    self.ckanapi.resource_show(id=election_value['draft_resource'])
                )
            except CKANAPIError as e:
                self.app.logger.error(
                    'Can\'t get draft resource metadata: %s' % (e)
                )
        return resources_metadata

    def get_records(self, resource_id):
        return self.filter_records(resource_id, sort='')

    def get_draft_record(self, verkiezing, gemeente_code, uuid):
        resource_id = self.elections[verkiezing]['draft_resource']
        filters = {'CBS gemeentecode': gemeente_code, 'UUID': uuid}
        records = self.filter_records(resource_id, filters=filters, limit=1, sort='')
        if len(records) == 1:
            return records[0]
        else:
            return None

    def filter_draft_records(self, verkiezing, gemeente_code):
        resource_id = self.elections[verkiezing]['draft_resource']
        return self._filter_gemeente_records(resource_id, gemeente_code)

    def filter_publish_records(self, verkiezing, gemeente_code):
        resource_id = self.elections[verkiezing]['publish_resource']
        return self._filter_gemeente_records(resource_id, gemeente_code)

    def _filter_gemeente_records(self, resource_id, gemeente_code):
        filters = {'CBS gemeentecode': gemeente_code}
        return self.filter_records(resource_id, filters=filters)

    def filter_records(self, resource_id, filters=None, limit=15000, sort='Nummer stembureau asc nulls last'):
        filters = {} if filters is None else filters
        try:
            return self.ckanapi.datastore_search(
                resource_id=resource_id, filters=filters, limit=limit, sort=sort)['records']
        except Exception as e:
            self.app.logger.error(
                'Can\'t filter records: %s' % (e)
            )
            return []

    def save_records(self, resource_id, records):
        self.ckanapi.datastore_upsert(
            resource_id=resource_id,
            force=True,
            records=records,
            method='upsert'
        )

    def delete_records(self, resource_id, filters=None):
        self.ckanapi.datastore_delete(
            resource_id=resource_id,
            force=True,
            filters=filters
        )

    # First delete all records in the publish_resource for the current
    # gemeente, then upsert all draft_records of the current gemeente
    # to the publish_resource
    def publish(self, verkiezing, gemeente_code, draft_records):
        election = self.elections[verkiezing]
        self.delete_records(
            election['publish_resource'],
            {'CBS gemeentecode': gemeente_code}
        )

        self.save_records(election['publish_resource'], draft_records)
