"""
The standard CSVkwItemExporter class does not pass the kwargs through to the
CSV writer, resulting in EXPORT_FIELDS and EXPORT_ENCODING being ignored
(EXPORT_EMPTY is not used by CSV).
"""
import csv

from scrapy.conf import settings
from scrapy.contrib.exporter import BaseItemExporter

#class CSVkwItemExporter(BaseItemExporter):
#
#    def __init__(self, *args, **kwargs):
#        kwargs['fields_to_export'] = settings.getlist('EXPORT_FIELDS') or None
#        kwargs['encoding'] = settings.get('EXPORT_ENCODING', 'utf-8')
#        #print '###CSV###', settings.getlist('EXPORT_FIELDS') or None
#        #print '###CSV###:', kwargs#
#
#        super(CSVkwItemExporter, self).__init__(*args, **kwargs)
#        print '###CSV###:', self.fields_to_export
        
class CSVkwItemExporter(BaseItemExporter):

    def __init__(self, file, include_headers_line=True, join_multivalued=',', **kwargs):
        item = settings.get('EXPORT_ITEM', '')
        kwargs['fields_to_export'] = settings.getlist('EXPORT_FIELDS'+item) or None
        kwargs['encoding'] = settings.get('EXPORT_ENCODING', 'utf-8')
        self._configure(kwargs, dont_fail=True)
        self.include_headers_line = include_headers_line
        kwargs['delimiter'] = settings.get('CSV_DELIMITER', ',')
        self.csv_writer = csv.writer(file, **kwargs)
        #self._headers_not_written = False
        self._headers_not_written = settings.get('EXPORT_HEADLINE', 'True') != 'False'
        self._join_multivalued = join_multivalued
        
        #print '###CSV###fields_to_export:', self.fields_to_export

    def _to_str_if_unicode(self, value):
        if isinstance(value, (list, tuple)):
            try:
                value = self._join_multivalued.join(value)
            except TypeError: # list in value may not contain strings
                pass
        return super(CSVkwItemExporter, self)._to_str_if_unicode(value)

    def export_item(self, item):
        if self._headers_not_written:
            self._headers_not_written = False
            self._write_headers_and_set_fields_to_export(item)

        fields = self._get_serialized_fields(item, default_value='', \
            include_empty=True)
        values = [x[1] for x in fields]
        self.csv_writer.writerow(values)
        #print '###CSV###values:', values

    def _write_headers_and_set_fields_to_export(self, item):
        if self.include_headers_line:
            if not self.fields_to_export:
                self.fields_to_export = item.fields.keys()
            self.csv_writer.writerow(self.fields_to_export)
        #print '###CSV###fields_to_export:', self.fields_to_export
        