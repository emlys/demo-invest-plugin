import logging
import os

import pygeoprocessing
import taskgraph

from natcap.invest import validation
from natcap.invest import utils
from natcap.invest import spec_utils
from natcap.invest.unit_registry import u
from natcap.invest import gettext
from natcap.invest import spec

LOGGER = logging.getLogger(__name__)

MODEL_SPEC = spec.ModelSpec(
    model_id="foo",
    model_title=gettext("Foo Model"),
    input_field_order=[
        ['workspace_dir', 'results_suffix'],
        ['raster_path', 'factor']],
    inputs=[
        spec.DirectoryInput(
            id="workspace_dir",
            name=gettext("workspace"),
            about=gettext(
                "The folder where all the model's output files will be written. If "
                "this folder does not exist, it will be created. If data already "
                "exists in the folder, it will be overwritten."),
            contents={},
            must_exist=False,
            permission="rwx"
        ),
        spec.StringInput(
            id="results_suffix",
            name=gettext("file suffix"),
            about=gettext(
                "Suffix that will be appended to all output file names. Useful to "
                "differentiate between model runs."),
            required=False,
            regexp="[a-zA-Z0-9_-]*"
        ),
        spec.NumberInput(
            id="n_workers",
            name=gettext("taskgraph n_workers parameter"),
            about=gettext(
                "The n_workers parameter to provide to taskgraph. "
                "-1 will cause all jobs to run synchronously. "
                "0 will run all jobs in the same process, but scheduling will take "
                "place asynchronously. Any other positive integer will cause that "
                "many processes to be spawned to execute tasks."),
            units=None,
            required=False,
            expression="value >= -1",
            hidden=True
        ),
        spec.SingleBandRasterInput(
            id="raster_path",
            name="Input Raster",
            data_type=float,
            units=None
        ),
        spec.IntegerInput(
            id="factor",
            name="Multiplication Factor",
            expression="value < 10"
        )
    ],
    outputs=[
        spec.SingleBandRasterOutput(
            id="result.tif",
            about="Raster multiplied by factor",
            data_type=float,
            units=None
        )
    ]
)

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
