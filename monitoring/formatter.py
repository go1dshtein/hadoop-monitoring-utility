import collections
import copy
import fnmatch
import glob
import logging
import os
import shutil

import jinja2

from monitoring.utils import human_size_format
from monitoring.utils import get_snmp_name

logger = logging.getLogger(__name__)


class HumanOutputFormatter:
    def __init__(self):
        self.max_key_length = 0

    def output(self, metrics, pattern):
        lines = []
        keys = fnmatch.filter(metrics.keys(), pattern)
        if not keys:
            return ""
        self.max_key_length = max(map(lambda x: len(x), keys))
        for key in sorted(keys):
            record = metrics[key]
            if record.get("value") is None:
                continue
            lines.append(self.format(key, record))
        return "\n".join(lines)

    def format(self, key, record):
        spaces = " " * (self.max_key_length - len(key) + 1)
        if record.get("unit") == "bytes":
            return "%s:%s%s" % (
                key, spaces, human_size_format(record.get("value")))
        else:
            return "%s:%s%s %s" % (
                key, spaces, record.get("value"), record.get("unit"))


class SubagentOutputFormatter:
    def output(self, metrics, pattern):
        lines = []
        for key, record in metrics.items():
            if record.get("value") is None:
                continue
            lines.append(self.format(key, record))
        return "\n".join(lines)

    def format(self, key, record):
        return "%s = %s" % (record.get("snmp"), record.get("value", 0))


class MIBOutputFormatter:
    def __init__(self, templatedir):
        logger.info("template dir: %s", templatedir)
        self.templatedir = templatedir
        self.env = jinja2.Environment()
        self.env.loader = jinja2.FileSystemLoader(self.templatedir)

    def output(self, objects, directory):
        self.create_directory(directory)
        objects = self.format(objects)
        for name, template in self.get_templates():
            logger.info("generating: %s", name)
            mib = template.render({"objects": objects})
            self.save_mib(mib, name, directory)

    def format(self, objects):
        result = collections.OrderedDict()
        for key, value in objects.items():
            pairs = zip(value["name"].split("."), value["oid"].split("."))
            parent = pairs[0][0]
            for name, oid in pairs[1:]:
                child = ".".join([parent, name])
                if (parent, child) not in result:
                    result_key = (get_snmp_name(parent), get_snmp_name(child))
                    if child == key:
                        result[result_key] = copy.deepcopy(value)
                    result.setdefault(result_key, {})["oid"] = oid
                    parent = child
        return result

    def get_templates(self):
        for filename in glob.glob("%s/*.txt" % self.templatedir):
            basename = os.path.basename(filename)
            yield basename, self.env.get_template(basename)

    def save_mib(self, mib, name, directory):
        with open(os.path.join(directory, name), "w") as h:
            h.write(mib)

    def create_directory(self, directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)
