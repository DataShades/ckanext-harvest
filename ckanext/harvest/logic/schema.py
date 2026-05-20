# -*- coding: utf-8 -*-
import ckan.plugins.toolkit as tk

from ckan.logic.schema import default_extras_schema
from ckan.logic.validators import (package_id_exists,
                                   name_validator,
                                   owner_org_validator,
                                   package_name_validator,
                                   boolean_validator,
                                   )
from ckan.logic.converters import convert_to_extras, convert_from_extras
from ckantoolkit import unicode_safe

from ckanext.harvest.logic.validators import (
    harvest_source_url_validator,
    harvest_source_type_exists,
    harvest_source_config_validator,
    harvest_source_extra_validator,
    harvest_source_frequency_exists,
    dataset_type_exists,
    harvest_source_convert_from_config,
    harvest_source_id_exists,
    harvest_job_exists,
    harvest_object_extras_validator,
)
ignore_missing = tk.get_validator("ignore_missing")
not_empty = tk.get_validator("not_empty")
ignore = tk.get_validator("ignore")
if_empty_same_as = tk.get_validator("if_empty_same_as")


def harvest_source_schema():

    schema = {
        'id': [ignore_missing, unicode_safe, package_id_exists],
        'type': [dataset_type_exists, unicode_safe],
        'url': [not_empty, unicode_safe, harvest_source_url_validator],
        'name': [not_empty, unicode_safe, name_validator, package_name_validator],
        'source_type': [not_empty, unicode_safe, harvest_source_type_exists, convert_to_extras],
        'title': [if_empty_same_as("name"), unicode_safe],
        'notes': [ignore_missing, unicode_safe],
        'owner_org': [owner_org_validator, unicode_safe],
        'private': [ignore_missing, boolean_validator],
        'organization': [ignore_missing],
        'frequency': [ignore_missing, unicode_safe, harvest_source_frequency_exists, convert_to_extras],
        'state': [ignore_missing],
        'config': [ignore_missing, harvest_source_config_validator, convert_to_extras],
        'extras': default_extras_schema(),
    }

    extras_schema = default_extras_schema()
    extras_schema['__extras'] = [ignore]

    schema['extras'] = extras_schema

    return schema


def harvest_source_create_package_schema():

    schema = harvest_source_schema()
    schema['__extras'] = [harvest_source_extra_validator]
    schema['save'] = [ignore]
    schema.pop("id")

    return schema


def harvest_source_update_package_schema():

    schema = harvest_source_create_package_schema()
    schema['owner_org'] = [ignore_missing, owner_org_validator, unicode_safe]
    return schema


def _remove_orphaned_extras(key, data, errors, context):
    """Drop extras left keyless by convert_from_extras.

    In CKAN 2.11+, convert_from_extras pulls source_type/frequency/config up
    to root and deletes their flattened ('extras', N, 'key'/'value') entries.
    But the extras subschema still runs afterwards (keys were captured by
    augment_data before deletion): not_empty drops the orphaned 'key', while
    unicode_safe(None) reanimates the 'value' as ''. The result is
    extras=[{'value': ''}, ...] with no 'key', which crashes consumers such as
    ckanext-dcat's after_dataset_show.
    """
    for index in {k[1] for k in data if k[0] == 'extras' and len(k) == 3}:
        if data.get(('extras', index, 'key')):
            continue

        for subkey in ('id', 'key', 'value', 'state', 'deleted',
                       'revision_timestamp'):
            data.pop(('extras', index, subkey), None)
            errors.pop(('extras', index, subkey), None)


def harvest_source_show_package_schema():

    schema = harvest_source_schema()
    schema.update({
        'source_type': [convert_from_extras, ignore_missing],
        'frequency': [convert_from_extras, ignore_missing],
        'config': [convert_from_extras, harvest_source_convert_from_config, ignore_missing],
        'metadata_created': [],
        'metadata_modified': [],
        'owner_org': [],
        'creator_user_id': [],
        'organization': [],
        'notes': [],
        'revision_id': [ignore_missing],
        'revision_timestamp': [ignore_missing],
        'tracking_summary': [ignore_missing],
    })

    schema['__extras'] = [ignore]
    schema['__after'] = [_remove_orphaned_extras]

    return schema


def harvest_object_create_schema():
    schema = {
        'guid': [ignore_missing, unicode_safe],
        'content': [ignore_missing, unicode_safe],
        'state': [ignore_missing, unicode_safe],
        'job_id': [harvest_job_exists],
        'source_id': [ignore_missing, harvest_source_id_exists],
        'package_id': [ignore_missing, package_id_exists],
        'extras': [ignore_missing, harvest_object_extras_validator],
    }
    return schema
