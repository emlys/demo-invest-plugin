import logging
import os

import pygeoprocessing
import taskgraph

from natcap.invest import validation
from natcap.invest import utils
from natcap.invest import spec_utils
from natcap.invest.unit_registry import u
from natcap.invest import gettext

LOGGER = logging.getLogger(__name__)

MODEL_SPEC = {
    "model_id": "foo",
    "model_name": gettext("Foo Model"),
    "pyname": "natcap.invest.foo",
    "userguide": "foo.html",
    "aliases": (),
    "ui_spec": {
        "order": [
            ['workspace_dir', 'results_suffix'],
            ['raster_path', 'factor']
        ],
        "hidden": ["n_workers"],
        "forum_tag": 'foo',
        "sampledata": {
            "filename": "Foo.zip"
        }
    },
    "args": {
        "workspace_dir": spec_utils.WORKSPACE,
        "results_suffix": spec_utils.SUFFIX,
        "n_workers": spec_utils.N_WORKERS,
        "raster_path": {
            "name": "Input Raster",
            "type": "raster",
            "bands": {1: {"type": "number", "units": u.none}}
        },
        "factor": {
            "name": "Multiplication Factor",
            "type": "integer",
            "expression": "value < 10"
        }
    },
    "outputs": {
        "result.tif": {
            "about": "Raster multiplied by factor",
            "bands": {1: {
                "type": "number",
                "units": u.none
            }}
        }
    }
}

_OUTPUT_BASE_FILES = {
    'result': 'result.tif',
}

def multiply_op(raster_path, factor, target_path):
    pygeoprocessing.raster_map(
        op=lambda x: x * factor,
        rasters=[raster_path],
        target_path=target_path)


def execute(args):
    file_suffix = utils.make_suffix_string(args, 'results_suffix')
    output_dir = args['workspace_dir']

    utils.make_directories([output_dir])

    LOGGER.info('Building file registry')
    file_registry = utils.build_file_registry(
        [(_OUTPUT_BASE_FILES, output_dir)], file_suffix)

    graph = taskgraph.TaskGraph(output_dir, args['n_workers'])

    graph.add_task(
        func=multiply_op,
        kwargs={
            'raster_path': args['raster_path'],
            'factor': int(args['factor']),
            'target_path': file_registry['result']
        },
        target_path_list=[file_registry['result']],
        task_name='multiply raster by factor')
    graph.join()
    LOGGER.info('Done!')


@validation.invest_validator
def validate(args, limit_to=None):
    return validation.validate(args, MODEL_SPEC['args'])
